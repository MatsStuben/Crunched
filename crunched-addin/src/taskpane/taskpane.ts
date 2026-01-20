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