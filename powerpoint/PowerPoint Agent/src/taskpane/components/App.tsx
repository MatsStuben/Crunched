import * as React from "react";
import { useState } from "react";
import { makeStyles, Button, Input, Text, Spinner } from "@fluentui/react-components";
import { AlignCenterHorizontal24Regular, Play24Regular } from "@fluentui/react-icons";
import { analyzeScene, requestArrangement, alignShapes, LabeledShape } from "../taskpane";

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
  quickButtons: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
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
    backgroundColor: "#e8f4e8",
    borderRadius: "4px",
    fontSize: "13px",
  },
  instructions: {
    fontSize: "12px",
    color: "#666",
  },
  startButton: {
    padding: "16px",
  },
});

const App: React.FC = () => {
  const styles = useStyles();
  const [message, setMessage] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [labeledShapes, setLabeledShapes] = useState<LabeledShape[] | null>(null);

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

  // Quick alignment (for selected shapes, no AI)
  const handleQuickAlign = async (type: string, label: string) => {
    setLoading(true);
    setResult("");
    try {
      await alignShapes(type);
      setResult(`Applied: ${label}`);
    } catch (error) {
      setResult(`Error: ${error}`);
    }
    setLoading(false);
  };

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <AlignCenterHorizontal24Regular />
        <Text className={styles.title}>PowerPoint Alignment Agent</Text>
      </div>

      {/* Start Button - shown when no shapes analyzed yet */}
      {!labeledShapes && (
        <>
          <Text className={styles.instructions}>
            Click Start to analyze the current slide. The AI will identify all shapes and you can
            then arrange them using natural language.
          </Text>
          <Button
            appearance="primary"
            size="large"
            icon={<Play24Regular />}
            onClick={handleStart}
            disabled={loading}
            className={styles.startButton}
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
            <Button appearance="primary" onClick={handleArrange} disabled={loading || !message.trim()}>
              Arrange
            </Button>
          </div>

          <Button size="small" onClick={handleStart} disabled={loading}>
            Re-analyze Slide
          </Button>
        </>
      )}

      {/* Quick Actions - always available for manual alignment */}
      <Text weight="semibold">Quick Actions (select shapes first):</Text>
      <div className={styles.quickButtons}>
        <Button size="small" onClick={() => handleQuickAlign("horizontal_center", "Horizontal Center")}>
          Align H
        </Button>
        <Button size="small" onClick={() => handleQuickAlign("vertical_center", "Vertical Center")}>
          Align V
        </Button>
        <Button size="small" onClick={() => handleQuickAlign("horizontal_distribute", "Distribute H")}>
          Distribute H
        </Button>
        <Button size="small" onClick={() => handleQuickAlign("vertical_distribute", "Distribute V")}>
          Distribute V
        </Button>
      </div>

      {/* Result area */}
      <div className={styles.result}>
        {loading ? (
          <Spinner size="small" label="Processing..." />
        ) : (
          <Text>{result || "Click Start to begin"}</Text>
        )}
      </div>
    </div>
  );
};

export default App;
