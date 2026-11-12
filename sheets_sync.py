"""Sinkronisasi hasil ke tab khusus Google Sheets."""
from pathlib import Path

import gspread
from gspread.exceptions import WorksheetNotFound

SPREADSHEET_ID = "1dbUFFyyseXObg7r4jLofnTrUcWycte4YryeSH62GuII"
TAB = "Data"


def sync(df):
    keys = list(Path("data").glob("*.json"))
    if len(keys) != 1:
        raise ValueError("Letakkan tepat satu file JSON service account di folder data.")
    client = gspread.service_account(filename=str(keys[0]), scopes=["https://www.googleapis.com/auth/spreadsheets"])
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        tab = sheet.worksheet(TAB)
    except WorksheetNotFound:
        tab = sheet.add_worksheet(title=TAB, rows=1, cols=1)
    current = tab.get_all_values()
    values = [list(df.columns)] + df.fillna("").astype(str).values.tolist()
    width = max(len(values[0]), max((len(row) for row in current), default=0))
    height = max(len(values), len(current))
    padded = [row + [""] * (width - len(row)) for row in values]
    padded.extend([[""] * width for _ in range(height - len(values))])
    if tab.row_count < height or tab.col_count < width:
        tab.resize(rows=max(tab.row_count, height), cols=max(tab.col_count, width))
    tab.update(values=padded, range_name="A1", value_input_option="RAW")
