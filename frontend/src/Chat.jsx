import { useState, useEffect, useRef } from "react";
import { streamChat, getChatHistory } from "./api";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pendingApproval, setPendingApproval] = useState(null);
  const [loading, setLoading] = useState(false);
  const streamingIndex = useRef(null);

  useEffect(() => {
    getChatHistory().then(setMessages).catch(() => {});
  }, []);

  async function consumeStream(generator) {
    // Add a placeholder assistant message we'll fill in token by token
    setMessages((prev) => {
      streamingIndex.current = prev.length;
      return [...prev, { role: "assistant", content: "" }];
    });

    for await (const event of generator) {
      if (event.type === "token") {
        setMessages((prev) => {
          const updated = [...prev];
          updated[streamingIndex.current] = {
            role: "assistant",
            content: updated[streamingIndex.current].content + event.content,
          };
          return updated;
        });
      } else if (event.type === "interrupt") {
        setPendingApproval(event.details);
        // Remove the empty placeholder - no final answer yet, we're paused
        setMessages((prev) => prev.slice(0, streamingIndex.current));
      }
      // 'done' needs no handling - stream just ends
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    const messageToSend = input;
    setInput("");
    setLoading(true);

    try {
      await consumeStream(streamChat(messageToSend));
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleApproval(approved) {
    setLoading(true);
    setPendingApproval(null);
    try {
      await consumeStream(streamChat(null, "/chat/approve/stream", { approved }));
    } finally {
      setLoading(false);
    }
  }

 return (
  <div className="chat-container">
    <div className="messages">
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.role}`}>
          {m.content}
        </div>
      ))}
      {loading && !pendingApproval && (
        <div className="message loading">
          <span className="pulse-dot" />
          ShopEase is typing
        </div>
      )}
    </div>

    {pendingApproval && (
      <div className="approval-box">
        <div className="approval-label">Approval needed</div>
        <p>{pendingApproval.message}</p>
        <div className="approval-actions">
          <button className="approve-btn" onClick={() => handleApproval(true)}>
            Approve
          </button>
          <button className="reject-btn" onClick={() => handleApproval(false)}>
            Reject
          </button>
        </div>
      </div>
    )}

    <form onSubmit={handleSend} className="chat-input">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={!!pendingApproval || loading}
      />
      <button type="submit" disabled={!!pendingApproval || loading}>
        Send
      </button>
    </form>
  </div>
  );
}