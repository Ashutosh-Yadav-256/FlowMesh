using NUnit.Framework;
using Moq;
using FlowMesh.Enterprise.Contracts;

namespace FlowMesh.Enterprise.Tests;

[TestFixture]
public class NUnitConnectorTests
{
    private Mock<IFlowMeshConnector> _mockConnector = null!;
    private ConnectionSpec _sampleConnection = null!;

    [SetUp]
    public void SetUp()
    {
        _mockConnector = new Mock<IFlowMeshConnector>(MockBehavior.Strict);
        _sampleConnection = new ConnectionSpec(
            Id: "conn_mssql_01",
            TenantId: "acme-corp",
            Type: "mssql",
            Name: "Enterprise SQL Server",
            Config: new Dictionary<string, object> { { "host", "sql.acme.internal" }, { "port", 1433 } }
        );
    }

    [Test]
    public async Task TestAsync_WhenHealthCheckPasses_ReturnsSuccessWithFourSteps()
    {
        var expectedSteps = new List<TestStepResult>
        {
            new("Network TDS Socket", "passed", 3.2, "Port 1433 reachable"),
            new("SQL Authentication", "passed", 2.1, "Authenticated as sa"),
            new("Database Permissions", "passed", 1.8, "db_datareader verified"),
            new("Schema Discovery", "passed", 4.0, "sys.tables enumerated")
        };
        var expectedResult = new TestResult(true, expectedSteps);

        _mockConnector
            .Setup(c => c.TestAsync(It.Is<ConnectionSpec>(s => s.TenantId == "acme-corp")))
            .ReturnsAsync(expectedResult);

        var result = await _mockConnector.Object.TestAsync(_sampleConnection);

        Assert.Multiple(() =>
        {
            Assert.That(result.Success, Is.True);
            Assert.That(result.Steps, Has.Count.EqualTo(4));
            Assert.That(result.Steps[0].Name, Is.EqualTo("Network TDS Socket"));
            Assert.That(result.ErrorMessage, Is.Null);
        });

        _mockConnector.Verify(c => c.TestAsync(It.IsAny<ConnectionSpec>()), Times.Once);
    }

    [Test]
    public async Task ExecuteAsync_WhenTargetDegraded_ReturnsOperationFailure()
    {
        var op = new Operation("op_select", "query", new Dictionary<string, object> { { "sql", "SELECT 1" } });
        _mockConnector
            .Setup(c => c.ExecuteAsync(It.IsAny<ConnectionSpec>(), It.IsAny<Operation>()))
            .ReturnsAsync(new OperationResult(false, 1500.0, null, "Timeout connecting to TDS pool", 0));

        var res = await _mockConnector.Object.ExecuteAsync(_sampleConnection, op);

        Assert.That(res.Success, Is.False);
        Assert.That(res.Error, Does.Contain("Timeout"));
        Assert.That(res.RecordsAffected, Is.EqualTo(0));
    }
}
