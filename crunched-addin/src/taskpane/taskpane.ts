/* global Excel console */

export async function readRange(range: string): Promise<unknown[][]> {
  let values: unknown[][] = [];
  await Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getActiveWorksheet();
    const r = sheet.getRange(range);
    r.load("values");
    await context.sync();
    values = r.values;
  });
  return values;
}

export async function writeRange(range: string, values: unknown[][]): Promise<void> {
  await Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getActiveWorksheet();
    const r = sheet.getRange(range);
    r.values = values;
    await context.sync();
  });
}

export async function getWorkbookInfo(): Promise<{ sheets: { name: string; usedRange: string }[] }> {
  const sheets: { name: string; usedRange: string }[] = [];
  await Excel.run(async (context) => {
    const worksheets = context.workbook.worksheets;
    worksheets.load("items/name");
    await context.sync();

    for (const sheet of worksheets.items) {
      const usedRange = sheet.getUsedRange();
      usedRange.load("address");
      await context.sync();
      sheets.push({
        name: sheet.name,
        usedRange: usedRange.address || "Empty"
      });
    }
  });
  return { sheets };
}