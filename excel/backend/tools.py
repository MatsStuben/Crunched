"""Tool definitions for Claude."""

TOOLS = [
    {"type": "web_search_20250305", "name": "web_search"},
    {
        "name": "read_range",
        "description": "Read values from a range of cells in the active Excel worksheet. Returns a 2D array of cell values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "range": {
                    "type": "string",
                    "description": "The Excel range to read, e.g. 'A1', 'A1:B10', 'A:A' for entire column"
                }
            },
            "required": ["range"]
        }
    },
    {
        "name": "write_range",
        "description": "Write values to cells. CRITICAL: The values array dimensions MUST exactly match the range. Examples: 'A1' (1 cell) -> [['value']]. 'A1:B1' (1 row, 2 cols) -> [['a','b']]. 'A1:A3' (3 rows, 1 col) -> [['a'],['b'],['c']]. 'A1:B2' (2 rows, 2 cols) -> [['a','b'],['c','d']].",
        "input_schema": {
            "type": "object",
            "properties": {
                "range": {
                    "type": "string",
                    "description": "The Excel range, e.g. 'A1', 'A1:B2'"
                },
                "values": {
                    "type": "array",
                    "description": "2D array where outer array = rows, inner arrays = columns. Must match range dimensions exactly.",
                    "items": {
                        "type": "array",
                        "items": {}
                    }
                }
            },
            "required": ["range", "values"]
        }
    },
    {
        "name": "get_workbook_info",
        "description": "Get information about the workbook structure. Returns sheet names and the used range for each sheet (e.g., 'A1:Z100'). Use this to understand what data exists before reading specific ranges.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]
