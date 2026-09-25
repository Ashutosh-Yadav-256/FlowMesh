"""
FlowMesh Stripe Connector (External Example Connector)

Demonstrates implementing the frozen Connector Protocol via BaseConnector.
Supports both live execution against Stripe API (with secret key) and
mock mode for air-gapped / CI environments.
"""

import httpx
import uuid
import time
from typing import Dict, Any, List, Optional

from flowmesh_connector.protocol import (
    ConnectionSpec,
    DiscoveryGraph,
    TableInfo,
    ColumnInfo,
    OperationSpec,
    Operation,
)
from flowmesh_connector.base import BaseConnector


class StripeConnector(BaseConnector):
    """Production-ready Stripe Payment & Billing Connector."""

    type: str = "stripe"

    def __init__(self) -> None:
        super().__init__()

        self.register_handler("create_customer", self.op_create_customer)
        self.register_handler("create_charge", self.op_create_charge)
        self.register_handler("capture_payment", self.op_capture_payment)
        self.register_handler("get_invoice", self.op_get_invoice)

    def _get_api_key(self, conn: ConnectionSpec) -> str:
        creds = conn.credentials or {}
        api_key = creds.get("api_key") or conn.config.get("api_key")
        if not api_key:
            raise ValueError("Missing Stripe API key in credentials or config")
        return str(api_key).strip()

    def _is_mock(self, conn: ConnectionSpec) -> bool:
        return conn.config.get("mock", False) is True or self._get_api_key(conn).startswith("sk_test_mock")

    async def ping_connection(self, conn: ConnectionSpec) -> None:
        if self._is_mock(conn):
            return
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.stripe.com/healthcheck")

            if resp.status_code >= 500:
                raise ConnectionError(f"Stripe API upstream unreachable: HTTP {resp.status_code}")

    async def validate_credentials(self, conn: ConnectionSpec) -> None:
        api_key = self._get_api_key(conn)
        if not (api_key.startswith("sk_test_") or api_key.startswith("sk_live_") or api_key.startswith("rk_")):
            raise ValueError("Invalid Stripe API key prefix. Must start with sk_test_, sk_live_, or rk_")
        if len(api_key) < 20:
            raise ValueError("Stripe API key is malformed or too short")

    async def check_permissions(self, conn: ConnectionSpec) -> None:
        if self._is_mock(conn):
            return
        api_key = self._get_api_key(conn)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.stripe.com/v1/balance",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code == 401:
                raise PermissionError("Stripe API authentication failed: Invalid API key")
            elif resp.status_code == 403:
                raise PermissionError("Stripe API restricted key does not have balance:read permission")

    async def probe_discovery(self, conn: ConnectionSpec) -> None:

        graph = await self.discover(conn)
        if not graph.entities:
            raise RuntimeError("Stripe schema discovery produced empty entity set")

    async def discover(self, conn: ConnectionSpec) -> DiscoveryGraph:
        """Discovers Stripe entity schemas."""
        entities = [
            TableInfo(
                schema_name="stripe",
                table_name="customers",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="email", data_type="varchar", nullable=True),
                    ColumnInfo(name="name", data_type="varchar", nullable=True),
                    ColumnInfo(name="currency", data_type="varchar", nullable=True),
                    ColumnInfo(name="balance", data_type="integer", nullable=False),
                    ColumnInfo(name="created", data_type="bigint", nullable=False),
                ]
            ),
            TableInfo(
                schema_name="stripe",
                table_name="charges",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="amount", data_type="integer", nullable=False),
                    ColumnInfo(name="currency", data_type="varchar", nullable=False),
                    ColumnInfo(name="customer_id", data_type="varchar", nullable=True),
                    ColumnInfo(name="status", data_type="varchar", nullable=False),
                    ColumnInfo(name="paid", data_type="boolean", nullable=False),
                    ColumnInfo(name="created", data_type="bigint", nullable=False),
                ]
            ),
            TableInfo(
                schema_name="stripe",
                table_name="invoices",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="customer_id", data_type="varchar", nullable=False),
                    ColumnInfo(name="amount_due", data_type="integer", nullable=False),
                    ColumnInfo(name="amount_paid", data_type="integer", nullable=False),
                    ColumnInfo(name="status", data_type="varchar", nullable=False),
                    ColumnInfo(name="period_end", data_type="bigint", nullable=False),
                ]
            ),
            TableInfo(
                schema_name="stripe",
                table_name="payment_intents",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="amount", data_type="integer", nullable=False),
                    ColumnInfo(name="currency", data_type="varchar", nullable=False),
                    ColumnInfo(name="customer_id", data_type="varchar", nullable=True),
                    ColumnInfo(name="status", data_type="varchar", nullable=False),
                    ColumnInfo(name="client_secret", data_type="varchar", nullable=False),
                ]
            ),
        ]
        return DiscoveryGraph(
            entities=entities,
            relationships=[
                {"from": "charges.customer_id", "to": "customers.id", "type": "many_to_one"},
                {"from": "invoices.customer_id", "to": "customers.id", "type": "many_to_one"},
                {"from": "payment_intents.customer_id", "to": "customers.id", "type": "many_to_one"},
            ],
            metadata={"api_version": "2024-06-20", "provider": "Stripe"}
        )

    def operations(self) -> List[OperationSpec]:
        return [
            OperationSpec(
                name="create_customer",
                description="Creates a new customer record in Stripe.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                        "metadata": {"type": "object"}
                    },
                    "required": ["email"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "email": {"type": "string"},
                        "created": {"type": "integer"}
                    }
                }
            ),
            OperationSpec(
                name="create_charge",
                description="Directly creates a credit card or token charge.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer"},
                        "currency": {"type": "string", "default": "usd"},
                        "customer_id": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["amount", "currency"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"},
                        "paid": {"type": "boolean"}
                    }
                }
            ),
            OperationSpec(
                name="capture_payment",
                description="Captures an authorized PaymentIntent.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "payment_intent_id": {"type": "string"},
                        "amount_to_capture": {"type": "integer"}
                    },
                    "required": ["payment_intent_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            ),
            OperationSpec(
                name="get_invoice",
                description="Retrieves a specific invoice details.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "invoice_id": {"type": "string"}
                    },
                    "required": ["invoice_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "amount_due": {"type": "integer"},
                        "status": {"type": "string"}
                    }
                }
            )
        ]

    async def op_create_customer(self, conn: ConnectionSpec, op: Operation) -> Dict[str, Any]:
        email = op.parameters.get("email")
        name = op.parameters.get("name", "")
        metadata = op.parameters.get("metadata", {})

        if not email:
            raise ValueError("Field 'email' is required to create a customer")

        if self._is_mock(conn):
            return {
                "id": f"cus_{uuid.uuid4().hex[:14]}",
                "object": "customer",
                "email": email,
                "name": name,
                "metadata": metadata,
                "balance": 0,
                "created": int(time.time()),
                "livemode": False
            }

        api_key = self._get_api_key(conn)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.stripe.com/v1/customers",
                headers={"Authorization": f"Bearer {api_key}"},
                data={"email": email, "name": name}
            )
            resp.raise_for_status()
            return resp.json()

    async def op_create_charge(self, conn: ConnectionSpec, op: Operation) -> Dict[str, Any]:
        amount = op.parameters.get("amount")
        currency = op.parameters.get("currency", "usd")
        customer_id = op.parameters.get("customer_id")
        desc = op.parameters.get("description", "FlowMesh Automated Charge")

        if amount is None or amount <= 0:
            raise ValueError("Field 'amount' must be a positive integer in cents")

        if self._is_mock(conn):
            return {
                "id": f"ch_{uuid.uuid4().hex[:14]}",
                "object": "charge",
                "amount": amount,
                "currency": currency.lower(),
                "customer": customer_id,
                "status": "succeeded",
                "paid": True,
                "description": desc,
                "created": int(time.time()),
                "livemode": False
            }

        api_key = self._get_api_key(conn)
        payload = {"amount": str(amount), "currency": currency.lower(), "description": desc}
        if customer_id:
            payload["customer"] = customer_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.stripe.com/v1/charges",
                headers={"Authorization": f"Bearer {api_key}"},
                data=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def op_capture_payment(self, conn: ConnectionSpec, op: Operation) -> Dict[str, Any]:
        pi_id = op.parameters.get("payment_intent_id")
        amount = op.parameters.get("amount_to_capture")
        if not pi_id:
            raise ValueError("Field 'payment_intent_id' is required")

        if self._is_mock(conn):
            return {
                "id": pi_id,
                "object": "payment_intent",
                "status": "succeeded",
                "amount_captured": amount or 5000,
                "created": int(time.time()),
                "livemode": False
            }

        api_key = self._get_api_key(conn)
        payload = {}
        if amount:
            payload["amount_to_capture"] = str(amount)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.stripe.com/v1/payment_intents/{pi_id}/capture",
                headers={"Authorization": f"Bearer {api_key}"},
                data=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def op_get_invoice(self, conn: ConnectionSpec, op: Operation) -> Dict[str, Any]:
        inv_id = op.parameters.get("invoice_id")
        if not inv_id:
            raise ValueError("Field 'invoice_id' is required")

        if self._is_mock(conn):
            return {
                "id": inv_id,
                "object": "invoice",
                "customer": f"cus_mock_{inv_id}",
                "amount_due": 10000,
                "amount_paid": 10000,
                "status": "paid",
                "period_end": int(time.time()),
                "livemode": False
            }

        api_key = self._get_api_key(conn)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.stripe.com/v1/invoices/{inv_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            resp.raise_for_status()
            return resp.json()
