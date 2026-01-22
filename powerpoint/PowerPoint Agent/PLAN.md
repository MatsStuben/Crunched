# PowerPoint Alignment Agent - Implementation Plan

## Overview

Build a vision-powered PowerPoint alignment agent that:
1. Analyzes slide content using Claude's vision capabilities
2. Understands natural language arrangement commands
3. Executes precise positioning using deterministic code

**Architecture Principle**: LLM handles understanding, code handles positioning.

---

## File Structure

```
backend/
├── main.py                 # FastAPI app, endpoints, session state
├── models.py               # Pydantic models (shared data structures)
├── agents/
│   ├── __init__.py
│   ├── scene_analyzer.py   # Vision LLM: screenshot + shapes → labeled objects
│   └── arranger.py         # LLM: labels + user command → order + alignment type

src/taskpane/
├── taskpane.ts             # PowerPoint API functions + backend calls
├── components/
│   └── App.tsx             # UI components
```

---

## Step 1: Define Data Models

**File**: `backend/models.py`

```python
class Shape:
    id: str
    left: float
    top: float
    width: float
    height: float

class LabeledShape:
    id: str
    label: str              # "email icon"
    description: str        # "blue envelope icon in top-left area"
    left: float
    top: float
    width: float
    height: float

class SceneAnalysisRequest:
    image_base64: str
    shapes: list[Shape]

class SceneAnalysisResponse:
    labeled_shapes: list[LabeledShape]

class ArrangeRequest:
    user_message: str
    labeled_shapes: list[LabeledShape]

class ArrangeResponse:
    order: list[str]        # Shape IDs in desired order
    alignment: str          # "horizontal_distribute" | "vertical_distribute" | etc.
    explanation: str        # Human-readable explanation
```

**Test**: Import models, create instances, validate with sample data.

---

## Step 2: Scene Analyzer Agent

**File**: `backend/agents/scene_analyzer.py`

**Purpose**: Takes slide screenshot + shape positions, returns labeled shapes.

**Input**:
- Screenshot (base64 PNG)
- List of shapes with positions `{id, left, top, width, height}`

**Output**:
- Same shapes with added `label` and `description` fields

**LLM Prompt Strategy**:
```
You are analyzing a PowerPoint slide. I'll give you:
1. An image of the slide
2. A list of shape positions (id, coordinates)

For each shape, provide:
- label: short name (e.g., "email icon", "right arrow", "robot")
- description: brief description including visual appearance

Return as JSON matching the schema.
```

**Tool Definition** (forces structured output):
```python
LABEL_SHAPES_TOOL = {
    "name": "label_shapes",
    "description": "Label each shape identified in the slide",
    "input_schema": {
        "type": "object",
        "properties": {
            "labeled_shapes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["id", "label", "description"]
                }
            }
        },
        "required": ["labeled_shapes"]
    }
}
```

**Test**:
1. Call with sample screenshot + shapes
2. Verify all shape IDs are returned
3. Verify labels are meaningful (not empty, not generic)

---

## Step 3: Arranger Agent

**File**: `backend/agents/arranger.py`

**Purpose**: Takes labeled shapes + user command, returns arrangement instructions.

**Input**:
- User message (e.g., "put email on left, then arrow, then robot")
- List of labeled shapes from scene analysis

**Output**:
- `order`: List of shape IDs in desired arrangement order
- `alignment`: Which alignment function to use
- `explanation`: What the agent understood and will do

**LLM Prompt Strategy**:
```
You are arranging shapes on a PowerPoint slide.

Available shapes:
{labeled_shapes as formatted list}

User request: {user_message}

Determine:
1. The order shapes should be arranged (left-to-right or top-to-bottom)
2. The alignment type to apply

Alignment types:
- horizontal_distribute: Spread shapes evenly left-to-right across slide
- vertical_distribute: Spread shapes evenly top-to-bottom across slide
- horizontal_center: Align all shapes to same vertical center line
- vertical_center: Align all shapes to same horizontal center line
```

**Tool Definition**:
```python
ARRANGE_TOOL = {
    "name": "arrange_shapes",
    "description": "Specify the arrangement of shapes",
    "input_schema": {
        "type": "object",
        "properties": {
            "order": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Shape IDs in the desired order"
            },
            "alignment": {
                "type": "string",
                "enum": ["horizontal_distribute", "vertical_distribute",
                         "horizontal_center", "vertical_center"]
            },
            "explanation": {
                "type": "string",
                "description": "Brief explanation of the arrangement"
            }
        },
        "required": ["order", "alignment", "explanation"]
    }
}
```

**Test**:
1. Call with sample labeled shapes + "put email first, then arrow, then robot"
2. Verify returned order matches expected
3. Verify alignment type is sensible
4. Test edge cases: "reverse the order", "swap email and robot"

---

## Step 4: Backend Endpoints

**File**: `backend/main.py`

### Endpoint: POST /analyze

```python
@app.post("/analyze")
async def analyze_scene(request: SceneAnalysisRequest) -> SceneAnalysisResponse:
    """
    Analyze slide screenshot and label all shapes.
    Called once when user clicks "Start".
    """
    labeled_shapes = scene_analyzer.analyze(
        image_base64=request.image_base64,
        shapes=request.shapes
    )
    return SceneAnalysisResponse(labeled_shapes=labeled_shapes)
```

**Test**:
```bash
curl -X POST https://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "...", "shapes": [{"id": "1", "left": 0, "top": 0, "width": 100, "height": 100}]}'
```

### Endpoint: POST /arrange

```python
@app.post("/arrange")
async def arrange_shapes(request: ArrangeRequest) -> ArrangeResponse:
    """
    Determine arrangement based on user command and known shapes.
    Called each time user gives an arrangement instruction.
    """
    result = arranger.arrange(
        user_message=request.user_message,
        labeled_shapes=request.labeled_shapes
    )
    return ArrangeResponse(**result)
```

**Test**:
```bash
curl -X POST https://localhost:8001/arrange \
  -H "Content-Type: application/json" \
  -d '{"user_message": "email then arrow then robot", "labeled_shapes": [...]}'
```

---

## Step 5: Frontend - Get All Shapes

**File**: `src/taskpane/taskpane.ts`

**New Function**: `getAllShapes()`

```typescript
export async function getAllShapes(): Promise<ShapeInfo[]> {
  // Get ALL shapes from current slide (not just selected)
  // Returns: [{id, left, top, width, height}, ...]
}
```

**Key Difference**: Current `getSelectedShapes()` only gets selected shapes. This gets ALL shapes on the slide.

**Test**:
1. Add 3 shapes to slide
2. Call `getAllShapes()` without selecting anything
3. Verify returns 3 shapes with correct positions

---

## Step 6: Frontend - Arrange In Order

**File**: `src/taskpane/taskpane.ts`

**New Function**: `arrangeShapesInOrder()`

```typescript
export async function arrangeShapesInOrder(
  shapeIds: string[],
  alignment: string
): Promise<void> {
  // 1. Get all shapes from slide
  // 2. Filter to only shapes in shapeIds
  // 3. Order them according to shapeIds array (NOT by current position)
  // 4. Apply alignment logic in that order
}
```

**Critical**: Must use Claude's order, not sort by current position.

**Test**:
1. Place 3 shapes randomly on slide
2. Call `arrangeShapesInOrder(["shape3", "shape1", "shape2"], "horizontal_distribute")`
3. Verify shapes are now positioned: shape3 left, shape1 middle, shape2 right

---

## Step 7: Frontend - Scene Analysis Flow

**File**: `src/taskpane/taskpane.ts`

**New Function**: `analyzeScene()`

```typescript
export async function analyzeScene(): Promise<LabeledShape[]> {
  // 1. Get slide screenshot
  const screenshot = await getSlideScreenshot();

  // 2. Get all shapes
  const shapes = await getAllShapes();

  // 3. Call backend /analyze
  const response = await fetch(`${BACKEND_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_base64: screenshot, shapes }),
  });

  // 4. Return labeled shapes
  const result = await response.json();
  return result.labeled_shapes;
}
```

**Test**:
1. Create slide with email icon, arrow, robot
2. Call `analyzeScene()`
3. Verify returns labels like "email", "arrow", "robot"

---

## Step 8: Frontend - Full Arrange Flow

**File**: `src/taskpane/taskpane.ts`

**New Function**: `requestArrangement()`

```typescript
export async function requestArrangement(
  userMessage: string,
  labeledShapes: LabeledShape[]
): Promise<string> {
  // 1. Call backend /arrange
  const response = await fetch(`${BACKEND_URL}/arrange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_message: userMessage, labeled_shapes: labeledShapes }),
  });

  // 2. Get arrangement result
  const result = await response.json();

  // 3. Execute arrangement
  await arrangeShapesInOrder(result.order, result.alignment);

  // 4. Return explanation
  return result.explanation;
}
```

**Test**:
1. Run scene analysis first
2. Call `requestArrangement("email, arrow, robot left to right", labeledShapes)`
3. Verify shapes are rearranged correctly

---

## Step 9: Frontend UI Updates

**File**: `src/taskpane/components/App.tsx`

**State**:
```typescript
const [labeledShapes, setLabeledShapes] = useState<LabeledShape[] | null>(null);
const [isAnalyzed, setIsAnalyzed] = useState(false);
```

**UI Flow**:
1. **Before analysis**: Show "Start" button
2. **After analysis**: Show labeled shapes + input for commands
3. **Command input**: Text field + "Arrange" button

**Components**:
```
┌────────────────────────────────────────┐
│ PowerPoint Alignment Agent             │
├────────────────────────────────────────┤
│ [Start Analysis]  (if not analyzed)    │
│                                        │
│ Detected Objects: (after analysis)     │
│ • email icon (top-left)                │
│ • arrow (center)                       │
│ • robot (right)                        │
│                                        │
│ ┌──────────────────────────┐ [Arrange] │
│ │ "email, arrow, robot..." │           │
│ └──────────────────────────┘           │
│                                        │
│ Quick Actions:                         │
│ [Align H] [Align V] [Dist H] [Dist V]  │
│                                        │
│ Result: "Arranged email → arrow →..."  │
└────────────────────────────────────────┘
```

**Test**: Manual UI testing with real PowerPoint.

---

## Step 10: Integration Testing

**Full Flow Test**:
1. Open PowerPoint with slide containing: email icon, 2 arrows, robot, Excel icon
2. Click "Start Analysis"
3. Verify all 5 objects are detected and labeled
4. Type: "email, arrow, robot, arrow, Excel from left to right"
5. Click "Arrange"
6. Verify shapes are repositioned in correct order, evenly distributed

**Edge Case Tests**:
- Empty slide → graceful error
- Single shape → message "need at least 2 shapes"
- Ambiguous command → LLM asks for clarification or makes best guess
- Shape not found → graceful error with message

---

## Implementation Order

1. ✅ Step 1: Models (testable independently)
2. ✅ Step 2: Scene Analyzer agent (testable with mock data)
3. ✅ Step 3: Arranger agent (testable with mock data)
4. ✅ Step 4: Backend endpoints (testable with curl)
5. ✅ Step 5: getAllShapes function (testable in browser console)
6. ✅ Step 6: arrangeShapesInOrder function (testable in browser console)
7. ✅ Step 7: analyzeScene flow (testable end-to-end)
8. ✅ Step 8: requestArrangement flow (testable end-to-end)
9. ✅ Step 9: UI updates (manual testing)
10. ✅ Step 10: Full integration test

---

## Success Criteria

- [ ] Scene analysis correctly identifies and labels all shapes on slide
- [ ] Natural language commands are interpreted correctly
- [ ] Shapes are arranged in the exact order specified by user
- [ ] Alignment/distribution is visually correct
- [ ] Response time < 5 seconds for typical operations
- [ ] Error messages are clear and actionable
- [ ] Code is modular, well-documented, and follows CLAUDE.md guidelines