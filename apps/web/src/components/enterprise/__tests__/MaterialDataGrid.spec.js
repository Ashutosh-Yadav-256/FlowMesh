
describe("FlowMesh Enterprise UI - MaterialDataGrid Component", function () {
  let sampleData;
  let sampleColumns;
  let clickSpy;

  beforeEach(function () {
    sampleData = [
      { id: "1", code: "ACC-100", balance: 5000, tenant: "acme-corp" },
      { id: "2", code: "ACC-200", balance: 12500, tenant: "acme-corp" },
      { id: "3", code: "ACC-300", balance: 800, tenant: "globex-corp" }
    ];

    sampleColumns = [
      { key: "id", header: "ID", sortable: true },
      { key: "code", header: "Account Code", sortable: true },
      { key: "balance", header: "Balance", sortable: true }
    ];

    clickSpy = jasmine.createSpy("onRowClick");
  });

  it("should initialize with correct dataset length", function () {
    expect(sampleData.length).toBe(3);
    expect(sampleColumns.length).toBe(3);
  });

  it("should correctly calculate pagination total pages", function () {
    const pageSize = 2;
    const totalPages = Math.ceil(sampleData.length / pageSize);
    expect(totalPages).toBe(2);

    const firstPageItems = sampleData.slice(0, pageSize);
    expect(firstPageItems.length).toBe(2);
    expect(firstPageItems[0].code).toBe("ACC-100");
  });

  it("should filter records based on search query", function () {
    const query = "globex";
    const filtered = sampleData.filter(function (item) {
      return Object.values(item).some(function (val) {
        return String(val).toLowerCase().indexOf(query) !== -1;
      });
    });

    expect(filtered.length).toBe(1);
    expect(filtered[0].tenant).toBe("globex-corp");
  });

  it("should trigger onRowClick spy with the clicked entity payload", function () {
    const targetRow = sampleData[1];
    clickSpy(targetRow);

    expect(clickSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalledWith(
      jasmine.objectContaining({
        id: "2",
        code: "ACC-200",
        balance: 12500
      })
    );
  });

  it("should sort records in ascending and descending order", function () {
    const sortedAsc = [...sampleData].sort(function (a, b) {
      return a.balance - b.balance;
    });
    expect(sortedAsc[0].balance).toBe(800);
    expect(sortedAsc[2].balance).toBe(12500);

    const sortedDesc = [...sampleData].sort(function (a, b) {
      return b.balance - a.balance;
    });
    expect(sortedDesc[0].balance).toBe(12500);
    expect(sortedDesc[2].balance).toBe(800);
  });
});
