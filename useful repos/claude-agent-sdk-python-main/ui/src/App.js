import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [maxTurns, setMaxTurns] = useState(5);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/query');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'assistant') {
        setMessages(prev => [...prev, { type: 'assistant', content: data.content }]);
      } else if (data.type === 'result') {
        setMessages(prev => [...prev, { type: 'result', content: data.content }]);
      } else if (data.type === 'complete') {
        setIsLoading(false);
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, { type: 'error', content: data.content }]);
        setIsLoading(false);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setIsLoading(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Connection error. Make sure the backend server is running on port 8000.' 
      }]);
      setIsLoading(false);
    };
    
    wsRef.current = ws;
  };

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!input.trim() || !isConnected || isLoading) {
      return;
    }
    
    // Add user message to chat
    setMessages(prev => [...prev, { type: 'user', content: input }]);
    
    // Send query to backend
    const queryData = {
      prompt: input,
      system_prompt: systemPrompt,
      max_turns: maxTurns
    };
    
    wsRef.current.send(JSON.stringify(queryData));
    setInput('');
    setIsLoading(true);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🤖 Claude Agent SDK</h1>
          <div className="header-controls">
            <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '● Connected' : '○ Disconnected'}
            </div>
            <button 
              className="settings-btn"
              onClick={() => setShowSettings(!showSettings)}
            >
              ⚙️ Settings
            </button>
            <button 
              className="clear-btn"
              onClick={clearChat}
            >
              🗑️ Clear
            </button>
          </div>
        </header>

        {showSettings && (
          <div className="settings-panel">
            <div className="setting-item">
              <label>System Prompt:</label>
              <input
                type="text"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Optional system prompt..."
              />
            </div>
            <div className="setting-item">
              <label>Max Turns:</label>
              <input
                type="number"
                value={maxTurns}
                onChange={(e) => setMaxTurns(parseInt(e.target.value) || 5)}
                min="1"
                max="20"
              />
            </div>
          </div>
        )}

        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <h2>Welcome to Claude Agent SDK!</h2>
                <p>Ask me anything and I'll help you using the Claude Agent.</p>
                <div className="example-prompts">
                  <button onClick={() => setInput("What is 2 + 2?")}>
                    What is 2 + 2?
                  </button>
                  <button onClick={() => setInput("Explain quantum computing")}>
                    Explain quantum computing
                  </button>
                  <button onClick={() => setInput("Write a Python function to sort a list")}>
                    Write a Python function
                  </button>
                </div>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.type}`}>
                <div className="message-header">
                  {msg.type === 'user' ? '👤 You' : 
                   msg.type === 'assistant' ? '🤖 Claude' : 
                   msg.type === 'error' ? '⚠️ Error' : '✅ Result'}
                </div>
                <div className="message-content">
                  {msg.content}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message assistant">
                <div className="message-header">🤖 Claude</div>
                <div className="message-content loading">
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                  <span className="dot">.</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <form className="input-form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Claude anything..."
              disabled={!isConnected || isLoading}
              className="message-input"
            />
            <button 
              type="submit" 
              disabled={!isConnected || isLoading || !input.trim()}
              className="send-btn"
            >
              {isLoading ? '⏳' : '📤'} Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
