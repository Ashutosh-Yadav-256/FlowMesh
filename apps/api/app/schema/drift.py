"""
FlowMesh Schema Drift Detection Engine

Computes semantic differences between a connection's baseline schema and
subsequent live discovered schemas. Classifies changes by impact and severity:
- CRITICAL (Breaking changes: dropped tables, dropped columns, type mutations, new mandatory columns)
- WARNING (Non-breaking changes: new tables, new optional columns, relaxed constraints)
- INFO (Metadata / comment updates)
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from flowmesh_connector.protocol import DiscoveryGraph, TableInfo, ColumnInfo


class DriftChangeType(str, Enum):
    TABLE_ADDED = "TABLE_ADDED"
    TABLE_DROPPED = "TABLE_DROPPED"
    COLUMN_ADDED = "COLUMN_ADDED"
    COLUMN_DROPPED = "COLUMN_DROPPED"
    TYPE_CHANGED = "TYPE_CHANGED"
    NULLABILITY_CHANGED = "NULLABILITY_CHANGED"
    PRIMARY_KEY_CHANGED = "PRIMARY_KEY_CHANGED"


class DriftSeverity(str, Enum):
    NONE = "NONE"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class DriftChange(BaseModel):
    change_type: DriftChangeType
    severity: DriftSeverity
    table_name: str
    column_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: str


class DriftReport(BaseModel):
    connection_id: str
    has_drift: bool
    highest_severity: DriftSeverity = DriftSeverity.NONE
    breaking_changes_count: int = 0
    warnings_count: int = 0
    changes: List[DriftChange] = Field(default_factory=list)
    baseline_entities_count: int = 0
    current_entities_count: int = 0
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SchemaDriftDetector:
    """Detects schema drift between baseline schema graph and current discovered graph."""

    @staticmethod
    def detect(
        connection_id: str,
        baseline: DiscoveryGraph,
        current: DiscoveryGraph,
    ) -> DriftReport:
        changes: List[DriftChange] = []
        breaking_count = 0
        warnings_count = 0

        baseline_tables: Dict[str, TableInfo] = {
            t.table_name.lower(): t for t in baseline.entities
        }
        current_tables: Dict[str, TableInfo] = {
            t.table_name.lower(): t for t in current.entities
        }

        for t_name, base_tbl in baseline_tables.items():
            if t_name not in current_tables:
                changes.append(
                    DriftChange(
                        change_type=DriftChangeType.TABLE_DROPPED,
                        severity=DriftSeverity.CRITICAL,
                        table_name=base_tbl.table_name,
                        old_value=base_tbl.table_name,
                        new_value=None,
                        description=f"Table '{base_tbl.table_name}' was dropped from upstream database.",
                    )
                )
                breaking_count += 1

        for t_name, cur_tbl in current_tables.items():
            if t_name not in baseline_tables:
                changes.append(
                    DriftChange(
                        change_type=DriftChangeType.TABLE_ADDED,
                        severity=DriftSeverity.WARNING,
                        table_name=cur_tbl.table_name,
                        old_value=None,
                        new_value=cur_tbl.table_name,
                        description=f"New table '{cur_tbl.table_name}' was discovered upstream.",
                    )
                )
                warnings_count += 1

        for t_name, base_tbl in baseline_tables.items():
            if t_name not in current_tables:
                continue
            cur_tbl = current_tables[t_name]

            base_cols: Dict[str, ColumnInfo] = {c.name.lower(): c for c in base_tbl.columns}
            cur_cols: Dict[str, ColumnInfo] = {c.name.lower(): c for c in cur_tbl.columns}

            for c_name, b_col in base_cols.items():
                if c_name not in cur_cols:
                    changes.append(
                        DriftChange(
                            change_type=DriftChangeType.COLUMN_DROPPED,
                            severity=DriftSeverity.CRITICAL,
                            table_name=base_tbl.table_name,
                            column_name=b_col.name,
                            old_value=f"{b_col.name} ({b_col.data_type})",
                            new_value=None,
                            description=f"Column '{b_col.name}' ({b_col.data_type}) was removed from '{base_tbl.table_name}'.",
                        )
                    )
                    breaking_count += 1

            for c_name, c_col in cur_cols.items():
                if c_name not in base_cols:
                    if not c_col.nullable:

                        sev = DriftSeverity.CRITICAL
                        breaking_count += 1
                        desc = f"New NOT NULL column '{c_col.name}' ({c_col.data_type}) added to '{base_tbl.table_name}'. May break workflow inserts."
                    else:
                        sev = DriftSeverity.WARNING
                        warnings_count += 1
                        desc = f"New optional column '{c_col.name}' ({c_col.data_type}) added to '{base_tbl.table_name}'."

                    changes.append(
                        DriftChange(
                            change_type=DriftChangeType.COLUMN_ADDED,
                            severity=sev,
                            table_name=cur_tbl.table_name,
                            column_name=c_col.name,
                            old_value=None,
                            new_value=f"{c_col.name} ({c_col.data_type})",
                            description=desc,
                        )
                    )

            for c_name, b_col in base_cols.items():
                if c_name not in cur_cols:
                    continue
                c_col = cur_cols[c_name]

                if b_col.data_type.lower() != c_col.data_type.lower():
                    changes.append(
                        DriftChange(
                            change_type=DriftChangeType.TYPE_CHANGED,
                            severity=DriftSeverity.CRITICAL,
                            table_name=base_tbl.table_name,
                            column_name=b_col.name,
                            old_value=b_col.data_type,
                            new_value=c_col.data_type,
                            description=f"Column '{b_col.name}' data type changed from '{b_col.data_type}' to '{c_col.data_type}'.",
                        )
                    )
                    breaking_count += 1

                if b_col.nullable != c_col.nullable:
                    if b_col.nullable and not c_col.nullable:

                        sev = DriftSeverity.CRITICAL
                        breaking_count += 1
                        desc = f"Column '{b_col.name}' changed from nullable to NOT NULL (breaking constraint)."
                    else:

                        sev = DriftSeverity.WARNING
                        warnings_count += 1
                        desc = f"Column '{b_col.name}' constraint relaxed to nullable."

                    changes.append(
                        DriftChange(
                            change_type=DriftChangeType.NULLABILITY_CHANGED,
                            severity=sev,
                            table_name=base_tbl.table_name,
                            column_name=b_col.name,
                            old_value=f"nullable={b_col.nullable}",
                            new_value=f"nullable={c_col.nullable}",
                            description=desc,
                        )
                    )

                if b_col.is_primary_key != c_col.is_primary_key:
                    changes.append(
                        DriftChange(
                            change_type=DriftChangeType.PRIMARY_KEY_CHANGED,
                            severity=DriftSeverity.CRITICAL,
                            table_name=base_tbl.table_name,
                            column_name=b_col.name,
                            old_value=f"pk={b_col.is_primary_key}",
                            new_value=f"pk={c_col.is_primary_key}",
                            description=f"Primary key status on column '{b_col.name}' was modified.",
                        )
                    )
                    breaking_count += 1

        highest_sev = DriftSeverity.NONE
        if breaking_count > 0:
            highest_sev = DriftSeverity.CRITICAL
        elif warnings_count > 0:
            highest_sev = DriftSeverity.WARNING

        return DriftReport(
            connection_id=connection_id,
            has_drift=len(changes) > 0,
            highest_severity=highest_sev,
            breaking_changes_count=breaking_count,
            warnings_count=warnings_count,
            changes=changes,
            baseline_entities_count=len(baseline.entities),
            current_entities_count=len(current.entities),
        )
