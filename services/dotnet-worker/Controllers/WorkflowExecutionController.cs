using Microsoft.AspNetCore.Mvc;
using FlowMesh.Enterprise.Contracts;

namespace FlowMesh.Enterprise.Controllers;

[ApiController]
[Route("api/v1/enterprise/dotnet")]
[Produces("application/json")]
public class WorkflowExecutionController : ControllerBase
{
    private readonly ILogger<WorkflowExecutionController> _logger;

    public WorkflowExecutionController(ILogger<WorkflowExecutionController> logger)
    {
        _logger = logger;
    }

    [HttpGet("status")]
    public IActionResult GetWorkerStatus()
    {
        return Ok(new
        {
            Service = "FlowMesh.Enterprise.DotNetWorker",
            Framework = "ASP.NET Core WebAPI 8.0",
            Status = "ONLINE",
            Timestamp = DateTime.UtcNow
        });
    }

    [HttpPost("execute-batch")]
    public async Task<IActionResult> ExecuteBatch(
        [FromHeader(Name = "X-Tenant-ID")] string? tenantId,
        [FromBody] BatchExecutionRequest request)
    {
        if (string.IsNullOrWhiteSpace(tenantId))
        {
            return BadRequest(new { Error = "Missing required X-Tenant-ID header" });
        }

        _logger.LogInformation("Processing batch {BatchId} for tenant {TenantId} with {Count} operations",
            request.BatchId, tenantId, request.Operations.Count);

        await Task.Delay(10);

        var results = request.Operations.Select(op => new
        {
            OperationId = op.Id,
            Status = "COMMITTED",
            DurationMs = 2.4,
            Timestamp = DateTime.UtcNow
        }).ToList();

        return Ok(new
        {
            BatchId = request.BatchId,
            TenantId = tenantId,
            ProcessedCount = results.Count,
            Status = "COMPLETED",
            Results = results
        });
    }
}

public record BatchExecutionRequest(string BatchId, List<Operation> Operations);
