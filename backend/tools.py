"""Tool definitions for Claude."""

TOOLS = [
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
        "description": "Write values to a range of cells in the active Excel worksheet. Values should be a 2D array matching the range dimensions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "range": {
                    "type": "string",
                    "description": "The Excel range to write to, e.g. 'A1', 'B2:C3'"
                },
                "values": {
                    "type": "array",
                    "description": "2D array of values to write. Each inner array is a row. E.g. [['Hello']] for single cell, [['A','B'],['C','D']] for 2x2",
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
