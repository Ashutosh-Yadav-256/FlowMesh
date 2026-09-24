# FlowMesh Enterprise Testing & QA Taxonomy

This document specifies the complete enterprise testing architecture for FlowMesh across unit testing, mocking, UI component testing, behavior-driven acceptance, and end-to-end browser automation.

---

## 1. Enterprise Testing Pyramid

```
                       ▲
                      / \
                     /   \   E2E Browser Automation
                    /     \  [ Selenium WebDriver ]
                   /───────\
                  /         \  Behavior-Driven Acceptance (BDD)
                 /           \ [ Cucumber / Gherkin Feature Specs ]
                /─────────────\
               /               \  UI Component & Browser Testing
              /                 \ [ Jasmine & Karma Test Runner ]
             /───────────────────\
            /                     \  Multi-Language Unit Testing & Mocking
           /                       \ [ NUnit / MSTest / Moq (.NET)   ]
          /                         \ [ pytest / mock (Python)        ]
         /                           \ [ JUnit 5 / Mockito (Java)     ]
        /                             \ [ go test / testify (Go)       ]
       └───────────────────────────────┘
```

---

## 2. Framework Taxonomy & Mapping

| Level | Framework / Tool | Language / Target | Enterprise Purpose | Artifact Location |
| :--- | :--- | :--- | :--- | :--- |
| **Unit Testing** | **NUnit 4** | C# / .NET 8 | Unit test execution with `[TestFixture]`, constraint-based assertions | `services/dotnet-worker/FlowMesh.Enterprise.Tests/NUnitConnectorTests.cs` |
| **Unit Testing** | **MSTest v3** | C# / .NET 8 | Enterprise Microsoft test execution (`[TestClass]`, `[TestMethod]`) | `services/dotnet-worker/FlowMesh.Enterprise.Tests/MSTestWorkflowTests.cs` |
| **Mocking** | **Moq 4** | C# / .NET 8 | Interface mocking (`Mock<T>`), call verification (`Times.Once`), argument matching (`It.IsAny<T>()`) | `services/dotnet-worker/FlowMesh.Enterprise.Tests/` |
| **UI Testing** | **Jasmine** | JavaScript / TS | BDD assertions (`describe`, `it`, `expect`), function spies (`spyOn`, `createSpy`) | `apps/web/src/components/enterprise/__tests__/MaterialDataGrid.spec.js` |
| **UI Runner** | **Karma** | JavaScript / TS | Headless Chrome/Firefox execution, JUnit XML & LCOV coverage export | `apps/web/karma.conf.js` |
| **BDD** | **Cucumber** | Gherkin / Multi | Business-readable acceptance tests (`Given`, `When`, `Then`) | `tests/bdd/enterprise_workflow.feature` |
| **E2E Browser** | **Selenium** | Python / Multi | Cross-browser automated user journeys across Chrome, Firefox, Edge | `tests/e2e/selenium/test_web_console_flows.py` |
| **Governance** | **SonarQube** | Polyglot | Unified quality gate: 80% coverage, 0 critical hotspots | `sonar-project.properties` |

---

## 3. UI Component Testing with Jasmine & Karma

### How it works:
1. **Jasmine** provides the declarative BDD specification:
   ```javascript
   describe("MaterialDataGrid", function () {
     it("calculates pagination total pages", function () {
       expect(Math.ceil(sampleData.length / pageSize)).toBe(2);
     });
   });
   ```
2. **Karma** spins up headless browser instances (ChromeHeadlessNoSandbox), serves files over HTTP, executes Jasmine specs, and generates XML/LCOV reports for SonarQube.
3. Run locally via:
   ```bash
   pnpm --filter web test:karma
   ```

---

## 4. Unit Testing & Mocking with NUnit, MSTest & Moq

### How it works:
1. **NUnit & MSTest** execute in parallel under the `Microsoft.NET.Test.Sdk` runner:
   ```bash
   dotnet test services/dotnet-worker/FlowMesh.Enterprise.Tests/
   ```
2. **Moq** decouples tests from real databases or external HTTP endpoints:
   ```csharp
   // Mocking a FlowMesh connector
   var mockConnector = new Mock<IFlowMeshConnector>(MockBehavior.Strict);
   mockConnector
       .Setup(c => c.TestAsync(It.IsAny<ConnectionSpec>()))
       .ReturnsAsync(new TestResult(true, steps));

   // Verifying execution count
   mockConnector.Verify(c => c.TestAsync(It.IsAny<ConnectionSpec>()), Times.Once);
   ```

---

## 5. Unified Quality Gate Execution (SonarQube)

All test runners output standard report formats:
- **Pytest**: `coverage.xml` (Cobertura/XML)
- **Karma**: `test-results.xml` (JUnit XML) and `lcov.info`
- **.NET (NUnit/MSTest)**: `test-results.trx` and `coverage.cobertura.xml` (Coverlet)
- **JUnit 5 / JaCoCo**: `jacoco.xml`

SonarQube ingests all reports concurrently, ensuring **100% visibility into code quality across all enterprise languages**.
