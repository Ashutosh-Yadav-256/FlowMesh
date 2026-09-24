namespace FlowMesh.Enterprise.Contracts;

public record ConnectionSpec(
    string Id,
    string TenantId,
    string Type,
    string Name,
    Dictionary<string, object> Config,
    Dictionary<string, object>? Credentials = null,
    string? AgentId = null
);

public record TestStepResult(string Name, string Status, double DurationMs, string Message);

public record TestResult(bool Success, List<TestStepResult> Steps, string? ErrorMessage = null);

public record Operation(string Id, string Name, Dictionary<string, object> Parameters);

public record OperationResult(bool Success, double DurationMs, object? Data = null, string? Error = null, int RecordsAffected = 0);

public interface IFlowMeshConnector
{
    string Type { get; }
    Task<TestResult> TestAsync(ConnectionSpec connection);
    Task<OperationResult> ExecuteAsync(ConnectionSpec connection, Operation operation);
}

public interface ITenantWorkflowRepository
{
    Task<bool> ValidateTenantAccessAsync(string tenantId, string workflowId);
    Task RecordAuditLogAsync(string tenantId, string action, string status);
}
