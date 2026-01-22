import * as React from "react";
import { useState } from "react";
import { makeStyles, Button, Input, Text, Spinner, Textarea, Divider } from "@fluentui/react-components";
import { AlignCenterHorizontal24Regular, Play24Regular, Document24Regular } from "@fluentui/react-icons";
import { analyzeScene, requestArrangement, generateScript, LabeledShape } from "../taskpane";

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  title: {
    fontSize: "20px",
    fontWeight: "600",
  },
  inputRow: {
    display: "flex",
    gap: "8px",
  },
  input: {
    flex: 1,
  },
  result: {
    padding: "12px",
    backgroundColor: "#f5f5f5",
    borderRadius: "4px",
    minHeight: "40px",
    whiteSpace: "pre-wrap",
  },
  shapesList: {
    padding: "12px",
    backgroundColor: "#fff7ed",
    borderRadius: "4px",
    fontSize: "13px",
    border: "1px solid #fed7aa",
  },
  instructions: {
    fontSize: "12px",
    color: "#666",
  },
  startButton: {
    padding: "16px",
  },
  section: {
    marginTop: "8px",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  textarea: {
    width: "100%",
    minHeight: "80px",
  },
  scriptResult: {
    padding: "12px",
    backgroundColor: "#fff7ed",
    borderRadius: "4px",
    whiteSpace: "pre-wrap",
    fontSize: "13px",
    maxHeight: "300px",
    overflowY: "auto",
    border: "1px solid #fed7aa",
  },
});

const App: React.FC = () => {
  const styles = useStyles();
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [labeledShapes, setLabeledShapes] = useState<LabeledShape[] | null>(null);

  // Script generation state
  const [scriptContext, setScriptContext] = useState("");
  const [generatedScript, setGeneratedScript] = useState("");
  const [scriptLoading, setScriptLoading] = useState(false);

  // Start session: analyze the slide
  const handleStart = async () => {
    setLoading(true);
    setResult("Analyzing slide...");
    setLabeledShapes(null);
    try {
      const shapes = await analyzeScene();
      setLabeledShapes(shapes);
      if (shapes.length === 0) {
        setResult("No shapes found on the slide. Add some shapes and try again.");
      } else {
        setResult(`Ready! Found ${shapes.length} objects. Type your arrangement command below.`);
      }
    } catch (error) {
      setResult(`Error: ${error}`);
    }
    setLoading(false);
  };

  // Arrange shapes based on user command
  const handleArrange = async () => {
    if (!message.trim() || !labeledShapes) return;
    setLoading(true);
    setResult("Arranging...");
    try {
      const explanation = await requestArrangement(message, labeledShapes);
      setResult(explanation);
      setMessage("");
    } catch (error) {
      setResult(`Error: ${error}`);
    }
    setLoading(false);
  };

  // Generate script for current slide
  const handleGenerateScript = async () => {
    setScriptLoading(true);
    setGeneratedScript("");
    try {
      const script = await generateScript(scriptContext);
      setGeneratedScript(script);
    } catch (error) {
      setGeneratedScript(`Error: ${error}`);
    }
    setScriptLoading(false);
  };

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <AlignCenterHorizontal24Regular />
        <Text className={styles.title}>Aligned</Text>
      </div>

      {/* Start Button - shown when no shapes analyzed yet */}
      {!labeledShapes && (
        <>
          <Text className={styles.instructions}>
            Click Start to analyze the current slide. The AI will identify all shapes and you can
            then arrange them using natural language.
          </Text>
          <Button
            size="large"
            icon={<Play24Regular />}
            onClick={handleStart}
            disabled={loading}
            className={styles.startButton}
            style={{ backgroundColor: "#f97316", color: "white" }}
          >
            {loading ? "Analyzing..." : "Start"}
          </Button>
        </>
      )}

      {/* Main UI - shown after analysis */}
      {labeledShapes && labeledShapes.length > 0 && (
        <>
          <div className={styles.shapesList}>
            <Text weight="semibold">Detected objects:</Text>
            <br />
            {labeledShapes.map((s, i) => (
              <span key={s.id}>
                {i > 0 && " • "}
                {s.label}
              </span>
            ))}
          </div>

          <Text className={styles.instructions}>
            Describe how you want the shapes arranged. Example: "email, then arrow, then robot, from
            left to right"
          </Text>

          <div className={styles.inputRow}>
            <Input
              className={styles.input}
              placeholder="e.g., 'arrange email, arrow, robot left to right'"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleArrange()}
              disabled={loading}
            />
            <Button
              onClick={handleArrange}
              disabled={loading || !message.trim()}
              style={{ backgroundColor: "#f97316", color: "white" }}
            >
              Arrange
            </Button>
          </div>

          <Button size="small" onClick={handleStart} disabled={loading}>
            Re-analyze Slide
          </Button>
        </>
      )}

      {/* Result area */}
      <div className={styles.result}>
        {loading ? (
          <Spinner size="small" label="Processing..." />
        ) : (
          <Text>{result || "Click Start to begin"}</Text>
        )}
      </div>

      <Divider />

      {/* Script Generation Section */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <Document24Regular />
          <Text weight="semibold">Generate Presentation Script</Text>
        </div>

        <Text className={styles.instructions}>
          Provide context about your presentation (audience, purpose, key points) and AI will generate a
          script for the current slide.
        </Text>

        <Textarea
          className={styles.textarea}
          placeholder="e.g., 'This is for a board presentation. The audience is executives. Focus on ROI and efficiency gains...'"
          value={scriptContext}
          onChange={(_, data) => setScriptContext(data.value)}
          disabled={scriptLoading}
        />

        <Button
          icon={<Document24Regular />}
          onClick={handleGenerateScript}
          disabled={scriptLoading}
          style={{ marginTop: "8px", backgroundColor: "#f97316", color: "white" }}
        >
          {scriptLoading ? "Generating..." : "Generate Script"}
        </Button>

        {(generatedScript || scriptLoading) && (
          <div className={styles.scriptResult} style={{ marginTop: "12px" }}>
            {scriptLoading ? (
              <Spinner size="small" label="Generating script..." />
            ) : (
              <Text>{generatedScript}</Text>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
