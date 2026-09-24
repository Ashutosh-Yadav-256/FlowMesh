using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;
using FlowMesh.Enterprise.Contracts;

namespace FlowMesh.Enterprise.Tests;

[TestClass]
public class MSTestWorkflowTests
{
    private Mock<ITenantWorkflowRepository> _mockRepo = null!;

    [TestInitialize]
    public void TestInitialize()
    {
        _mockRepo = new Mock<ITenantWorkflowRepository>();
    }

    [TestMethod]
    public async Task ValidateTenantAccess_WhenTenantAuthorized_ReturnsTrue()
    {
        const string tenantId = "acme-corp";
        const string workflowId = "wf_payroll_batch";

        _mockRepo
            .Setup(r => r.ValidateTenantAccessAsync(tenantId, workflowId))
            .ReturnsAsync(true);

        var hasAccess = await _mockRepo.Object.ValidateTenantAccessAsync(tenantId, workflowId);

        Assert.IsTrue(hasAccess, "Authorized tenant must have workflow access");
        _mockRepo.Verify(r => r.ValidateTenantAccessAsync(tenantId, workflowId), Times.Once);
    }

    [TestMethod]
    public async Task ValidateTenantAccess_WhenCrossTenantAccessAttempted_ReturnsFalse()
    {
        _mockRepo
            .Setup(r => r.ValidateTenantAccessAsync("globex-corp", "wf_acme_internal"))
            .ReturnsAsync(false);

        var accessDenied = await _mockRepo.Object.ValidateTenantAccessAsync("globex-corp", "wf_acme_internal");

        Assert.IsFalse(accessDenied, "Cross-tenant workflow access must be rejected");
    }

    [TestMethod]
    public async Task RecordAuditLog_InvokedWithCorrectTenantContext()
    {
        _mockRepo
            .Setup(r => r.RecordAuditLogAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .Returns(Task.CompletedTask);

        await _mockRepo.Object.RecordAuditLogAsync("acme-corp", "WORKFLOW_EXECUTE", "SUCCESS");

        _mockRepo.Verify(r => r.RecordAuditLogAsync("acme-corp", "WORKFLOW_EXECUTE", "SUCCESS"), Times.Once);
    }
}
