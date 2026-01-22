/* global PowerPoint console */

const BACKEND_URL = "https://localhost:8001";

export interface ShapeInfo {
  id: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface LabeledShape {
  id: string;
  label: string;
  description: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

export async function getSelectedShapes(): Promise<ShapeInfo[]> {
  const shapes: ShapeInfo[] = [];

  await PowerPoint.run(async (context) => {
    const selectedShapes = context.presentation.getSelectedShapes();
    selectedShapes.load("items");
    await context.sync();

    for (const shape of selectedShapes.items) {
      shape.load(["id", "left", "top", "width", "height"]);
    }
    await context.sync();

    for (const shape of selectedShapes.items) {
      shapes.push({
        id: shape.id,
        left: shape.left,
        top: shape.top,
        width: shape.width,
        height: shape.height,
      });
    }
  });

  return shapes;
}

export async function alignShapes(alignmentType: string): Promise<void> {
  await PowerPoint.run(async (context) => {
    const selectedShapes = context.presentation.getSelectedShapes();
    selectedShapes.load("items");
    await context.sync();

    if (selectedShapes.items.length < 2) {
      console.log("Need at least 2 shapes to align");
      return;
    }

    for (const shape of selectedShapes.items) {
      shape.load(["id", "left", "top", "width", "height"]);
    }
    await context.sync();

    const shapes = selectedShapes.items;

    if (alignmentType === "horizontal_center") {
      // Align all shapes to the same X center (vertical line through center)
      const avgCenterX = shapes.reduce((sum, s) => sum + s.left + s.width / 2, 0) / shapes.length;
      for (const shape of shapes) {
        shape.left = avgCenterX - shape.width / 2;
      }
    } else if (alignmentType === "vertical_center") {
      // Align all shapes to the same Y center (horizontal line through center)
      const avgCenterY = shapes.reduce((sum, s) => sum + s.top + s.height / 2, 0) / shapes.length;
      for (const shape of shapes) {
        shape.top = avgCenterY - shape.height / 2;
      }
    } else if (alignmentType === "horizontal_distribute") {
      // Distribute shapes evenly across slide width
      // Standard slide width is 960 points (10 inches at 96 dpi)
      const slideWidth = 960;
      const margin = 40;
      const availableWidth = slideWidth - 2 * margin;
      const totalShapeWidth = shapes.reduce((sum, s) => sum + s.width, 0);
      const gap = (availableWidth - totalShapeWidth) / (shapes.length - 1);

      const sorted = [...shapes].sort((a, b) => a.left - b.left);
      let currentLeft = margin;
      for (const shape of sorted) {
        shape.left = currentLeft;
        currentLeft += shape.width + gap;
      }
    } else if (alignmentType === "vertical_distribute") {
      // Distribute shapes evenly across slide height
      // Standard slide height is 540 points (16:9 ratio)
      const slideHeight = 540;
      const margin = 40;
      const availableHeight = slideHeight - 2 * margin;
      const totalShapeHeight = shapes.reduce((sum, s) => sum + s.height, 0);
      const gap = (availableHeight - totalShapeHeight) / (shapes.length - 1);

      const sorted = [...shapes].sort((a, b) => a.top - b.top);
      let currentTop = margin;
      for (const shape of sorted) {
        shape.top = currentTop;
        currentTop += shape.height + gap;
      }
    }

    await context.sync();
  });
}

export async function alignWithAI(userMessage: string): Promise<string> {
  try {
    console.log("Getting selected shapes...");
    const shapes = await getSelectedShapes();
    console.log(`Found ${shapes.length} shapes:`, shapes);

    if (shapes.length < 2) {
      return "Please select at least 2 shapes to align.";
    }

    console.log(`Calling backend at ${BACKEND_URL}/align...`);
    const response = await fetch(`${BACKEND_URL}/align`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        shape_count: shapes.length,
      }),
    });

    console.log(`Backend response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error response:", errorText);
      throw new Error(`Backend error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log("Backend result:", result);

    await alignShapes(result.alignment_type);

    return result.explanation;
  } catch (error) {
    console.error("Alignment error:", error);
    return `Error: ${error}`;
  }
}

// Test function to check if slide screenshot API is available
export async function testSlideScreenshot(): Promise<string> {
  try {
    let result = "";
    await PowerPoint.run(async (context) => {
      const slide = context.presentation.getSelectedSlides().getItemAt(0);

      // Try to get slide as image
      const imageData = slide.getImageAsBase64({ height: 400, width: 711 }); // 16:9 aspect ratio
      await context.sync();

      result = imageData.value.substring(0, 100) + "..."; // Just show first 100 chars
      console.log("Screenshot API works! Base64 length:", imageData.value.length);
    });
    return `Success! Got base64 image (${result})`;
  } catch (error) {
    console.error("Screenshot API error:", error);
    return `Error: ${error}`;
  }
}

// Get ALL shapes from the current slide (not just selected)
export async function getAllShapes(): Promise<ShapeInfo[]> {
  const shapes: ShapeInfo[] = [];

  await PowerPoint.run(async (context) => {
    const slide = context.presentation.getSelectedSlides().getItemAt(0);
    const allShapes = slide.shapes;
    allShapes.load("items");
    await context.sync();

    for (const shape of allShapes.items) {
      shape.load(["id", "left", "top", "width", "height"]);
    }
    await context.sync();

    for (const shape of allShapes.items) {
      shapes.push({
        id: shape.id,
        left: shape.left,
        top: shape.top,
        width: shape.width,
        height: shape.height,
      });
    }
  });

  console.log(`getAllShapes: Found ${shapes.length} shapes`, shapes);
  return shapes;
}

// Analyze slide: get screenshot + shapes, send to backend for labeling
export async function analyzeScene(): Promise<LabeledShape[]> {
  console.log("Starting scene analysis...");

  // Get screenshot and shapes in parallel
  const [screenshot, shapes] = await Promise.all([getSlideScreenshot(), getAllShapes()]);

  console.log(`Got screenshot (${screenshot.length} chars) and ${shapes.length} shapes`);

  if (shapes.length === 0) {
    console.warn("No shapes found on slide");
    return [];
  }

  // Call backend /analyze endpoint
  const response = await fetch(`${BACKEND_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_base64: screenshot,
      shapes: shapes,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Analyze failed: ${response.status} - ${errorText}`);
  }

  const result = await response.json();
  console.log("Scene analysis result:", result.labeled_shapes);

  return result.labeled_shapes;
}

// Get slide screenshot as base64
export async function getSlideScreenshot(): Promise<string> {
  let imageBase64 = "";
  await PowerPoint.run(async (context) => {
    const slide = context.presentation.getSelectedSlides().getItemAt(0);
    const imageData = slide.getImageAsBase64({ height: 400, width: 711 });
    await context.sync();
    imageBase64 = imageData.value;
  });
  return imageBase64;
}

// Send screenshot to Claude and get description
export async function describeSlide(): Promise<string> {
  try {
    console.log("Getting slide screenshot...");
    const imageBase64 = await getSlideScreenshot();
    console.log(`Got screenshot, length: ${imageBase64.length}`);

    console.log("Sending to Claude...");
    const response = await fetch(`${BACKEND_URL}/describe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: imageBase64 }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const result = await response.json();
    console.log("Claude description:", result.description);
    return result.description;
  } catch (error) {
    console.error("Describe error:", error);
    return `Error: ${error}`;
  }
}

// Arrange shapes in a specific order (uses Claude's order, not current positions)
export async function arrangeShapesInOrder(
  shapeIds: string[],
  alignment: string
): Promise<void> {
  console.log(`Arranging ${shapeIds.length} shapes with alignment: ${alignment}`);
  console.log("Shape order:", shapeIds);

  await PowerPoint.run(async (context) => {
    const slide = context.presentation.getSelectedSlides().getItemAt(0);
    const allShapes = slide.shapes;
    allShapes.load("items");
    await context.sync();

    // Load all shape properties
    for (const shape of allShapes.items) {
      shape.load(["id", "left", "top", "width", "height"]);
    }
    await context.sync();

    // Create a map of id -> shape
    const shapeMap = new Map<string, PowerPoint.Shape>();
    for (const shape of allShapes.items) {
      shapeMap.set(shape.id, shape);
    }

    // Get shapes in the specified order
    const orderedShapes: PowerPoint.Shape[] = [];
    for (const id of shapeIds) {
      const shape = shapeMap.get(id);
      if (shape) {
        orderedShapes.push(shape);
      } else {
        console.warn(`Shape with id ${id} not found`);
      }
    }

    if (orderedShapes.length < 2) {
      console.log("Need at least 2 shapes to arrange");
      return;
    }

    // Calculate average Y position (for horizontal arrangements, keep same height)
    const avgCenterY =
      orderedShapes.reduce((sum, s) => sum + s.top + s.height / 2, 0) / orderedShapes.length;

    if (alignment === "horizontal_distribute") {
      // Distribute shapes left-to-right in the specified order
      const slideWidth = 960;
      const margin = 40;
      const availableWidth = slideWidth - 2 * margin;
      const totalShapeWidth = orderedShapes.reduce((sum, s) => sum + s.width, 0);
      const gap = (availableWidth - totalShapeWidth) / (orderedShapes.length - 1);

      let currentLeft = margin;
      for (const shape of orderedShapes) {
        shape.left = currentLeft;
        shape.top = avgCenterY - shape.height / 2; // Also align vertically
        currentLeft += shape.width + gap;
      }
    } else if (alignment === "vertical_distribute") {
      // Distribute shapes top-to-bottom in the specified order
      const slideHeight = 540;
      const margin = 40;
      const availableHeight = slideHeight - 2 * margin;
      const totalShapeHeight = orderedShapes.reduce((sum, s) => sum + s.height, 0);
      const gap = (availableHeight - totalShapeHeight) / (orderedShapes.length - 1);

      // Calculate average X position
      const avgCenterX =
        orderedShapes.reduce((sum, s) => sum + s.left + s.width / 2, 0) / orderedShapes.length;

      let currentTop = margin;
      for (const shape of orderedShapes) {
        shape.top = currentTop;
        shape.left = avgCenterX - shape.width / 2; // Also align horizontally
        currentTop += shape.height + gap;
      }
    } else if (alignment === "horizontal_center") {
      // Align all to same X center
      const avgCenterX =
        orderedShapes.reduce((sum, s) => sum + s.left + s.width / 2, 0) / orderedShapes.length;
      for (const shape of orderedShapes) {
        shape.left = avgCenterX - shape.width / 2;
      }
    } else if (alignment === "vertical_center") {
      // Align all to same Y center
      for (const shape of orderedShapes) {
        shape.top = avgCenterY - shape.height / 2;
      }
    }

    await context.sync();
    console.log("Arrangement complete");
  });
}

// Request arrangement from backend and execute it
export async function requestArrangement(
  userMessage: string,
  labeledShapes: LabeledShape[]
): Promise<string> {
  console.log(`Requesting arrangement: "${userMessage}"`);
  console.log(`Available shapes:`, labeledShapes.map((s) => s.label));

  try {
    const response = await fetch(`${BACKEND_URL}/arrange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_message: userMessage,
        labeled_shapes: labeledShapes,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Arrange failed: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log("Arrangement result:", result);

    // Execute the arrangement
    await arrangeShapesInOrder(result.order, result.alignment);

    return result.explanation;
  } catch (error) {
    console.error("Arrangement error:", error);
    return `Error: ${error}`;
  }
}

// Legacy function for simple text insertion
export async function insertText(text: string) {
  try {
    await PowerPoint.run(async (context) => {
      const slide = context.presentation.getSelectedSlides().getItemAt(0);
      const textBox = slide.shapes.addTextBox(text);
      textBox.fill.setSolidColor("white");
      textBox.lineFormat.color = "black";
      textBox.lineFormat.weight = 1;
      textBox.lineFormat.dashStyle = PowerPoint.ShapeLineDashStyle.solid;
      await context.sync();
    });
  } catch (error) {
    console.log("Error: " + error);
  }
}
