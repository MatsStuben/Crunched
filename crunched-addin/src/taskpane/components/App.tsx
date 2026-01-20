import * as React from "react";
import { useState } from "react";
import { readRange, writeRange, getWorkbookInfo } from "../taskpane";

const API_URL = "https://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

interface ChatResponse {
  session_id: string;
  response: string | null;
  tool_calls: ToolCall[] | null;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const executeToolCall = async (toolCall: ToolCall): Promise<unknown> => {
    if (toolCall.name === "read_range") {
      return await readRange(toolCall.args.range as string);
    }
    if (toolCall.name === "write_range") {
      await writeRange(
        toolCall.args.range as string,
        toolCall.args.values as unknown[][]
      );
      return "Done";
    }
    if (toolCall.name === "get_workbook_info") {
      return await getWorkbookInfo();
    }
    return "Unknown tool";
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      let response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, session_id: sessionId }),
      });
      let data: ChatResponse = await response.json();
      setSessionId(data.session_id);

      // Tool execution loop
      while (data.tool_calls && data.tool_calls.length > 0) {
        const toolResults = [];
        for (const toolCall of data.tool_calls) {
          const result = await executeToolCall(toolCall);
          toolResults.push({
            tool_use_id: toolCall.id,
            name: toolCall.name,
            result
          });
        }

        response = await fetch(`${API_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage,
            session_id: data.session_id,
            tool_results: toolResults
          }),
        });
        data = await response.json();
      }

      if (data.response) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${error}` }]);
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: 10, fontFamily: "sans-serif" }}>
      <h2>Crunched 2.0</h2>

      <div style={{ height: 300, overflowY: "auto", border: "1px solid #ccc", padding: 10, marginBottom: 10 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <strong>{msg.role === "user" ? "You" : "Agent"}:</strong> {msg.content}
          </div>
        ))}
        {loading && <div>Thinking...</div>}
      </div>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        placeholder="Type a message..."
        style={{ width: "70%", padding: 8 }}
      />
      <button onClick={sendMessage} style={{ padding: 8, marginLeft: 5 }}>
        Send
      </button>
    </div>
  );
};

export default App;
