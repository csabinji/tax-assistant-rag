// src/App.jsx - Enhanced Professional Nepali Tax Chatbot Frontend
import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';
const SendIcon = React.memo(() => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
  </svg>
));

const TaxBotIcon = React.memo(() => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15.5h2v-2h-2v2zm0-4h2v-2h-2v2zm4 0h-2v-2h2v2zm0-4h-2v-2h2v2zM12 4.5c-4.66 0-8.5 3.84-8.5 8.5s3.84 8.5 8.5 8.5 8.5-3.84 8.5-8.5-3.84-8.5-8.5-8.5zM7 9h10V7H7v2zm0 8h10v-2H7v2z"/>
  </svg>
));

const UserIcon = React.memo(() => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"></path>
  </svg>
));

const WarningIcon = React.memo(() => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
  </svg>
));

const ChatLayout = React.memo(({ children }) => (
  <div className="chat-app-container">{children}</div>
));

const ChatHeader = React.memo(() => (
  <header className="chat-header">
    <div className="chat-header__content">
      <h1 className="chat-header__title">Tax Assistant</h1>
      <p className="chat-header__subtitle">Expert guidance on Nepal tax laws</p>
    </div>
    <div className="chat-header__decoration">
      <div className="decoration-circle"></div>
      <div className="decoration-circle"></div>
      <div className="decoration-circle"></div>
    </div>
  </header>
));

const DisclaimerBox = React.memo(() => (
  <div className="disclaimer-box" role="alert" aria-live="polite">
    <div className="disclaimer-box__icon">
      <WarningIcon />
    </div>
    <div className="disclaimer-box__content">
      <h3 className="disclaimer-box__title">Important Disclaimer</h3>
      <p className="disclaimer-box__text">
        The information provided by this assistant is for general guidance only and does not constitute professional tax advice. For specific advice tailored to your situation, please consult with a qualified tax professional.
      </p>
    </div>
  </div>
));

const MessageBubble = React.memo(({ message, isMyMessage }) => {
  const bubbleClass = `message-bubble ${isMyMessage ? 'message-bubble--my' : 'message-bubble--other'}`;
  const IconComponent = isMyMessage ? UserIcon : TaxBotIcon;

  return (
    <div className={bubbleClass} role="listitem" aria-label={`Message from ${message.user}`}>
      <div className="message-bubble__icon">
        <IconComponent />
      </div>
      <div className="message-bubble__content">
        <div className="message-bubble__header">
          <span className="message-bubble__sender">{message.user}</span>
          <span className="message-bubble__timestamp">{message.timestamp}</span>
        </div>
        <div className="message-bubble__text">{message.text}</div>
        {!isMyMessage && message.context && message.context.length > 0 && (
          <div className="message-bubble__context">
            <details>
              <summary>Supporting References ({message.context.length})</summary>
              <div className="context-content">
                {message.context.map((ctx, index) => (
                  <div key={index} className="context-item">
                    <span className="context-index">{index + 1}.</span>
                    <p className="context-paragraph">{ctx}</p>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
});

const MessageList = React.memo(({ messages, currentUser, isLoading, backendError, onRetry }) => { // Added onRetry prop
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, isLoading, backendError]);

  const handleSuggestionClick = useCallback((question) => {
    // This assumes there's a way to trigger the send message from here,
    // which might require lifting state or calling a function passed down from App.
    // For now, it's a placeholder.
    console.log(`Suggested question clicked: ${question}`);
    // You would typically setInputMessage(question) and then trigger sendMessage
    // This requires passing setInputMessage and handleSendMessage down, or refactoring.
  }, []);

  return (
    <div className="message-list" role="list" aria-live="polite" aria-atomic="true">
      {messages.length === 0 && !isLoading && !backendError && (
        <div className="welcome-screen">
          <div className="welcome-content">
            <h2>Welcome to Tax Assistant</h2>
            <p>Ask me anything about:</p>
            <ul className="suggested-questions">
              {['Income tax rates', 'VAT regulations', 'Tax filing deadlines', 'Business tax obligations'].map((question) => (
                <li key={question} onClick={() => handleSuggestionClick(question)} tabIndex="0" role="button">
                  {question}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          isMyMessage={msg.user === currentUser}
        />
      ))}

      {isLoading && (
        <div className="loading-indicator message-bubble message-bubble--other">
          <div className="message-bubble__icon"><TaxBotIcon /></div>
          <div className="message-bubble__content">
            <p className="message-bubble__text">Researching your question...</p>
            <div className="dots-loader">
              <div></div><div></div><div></div>
            </div>
          </div>
        </div>
      )}

      {backendError && (
        <div className="error-message message-bubble message-bubble--other">
          <div className="message-bubble__icon"><WarningIcon /></div>
          <div className="message-bubble__content">
            <p className="message-bubble__text">Connection Issue</p>
            <div className="error-details">
              <p>We couldn't process your request.</p>
              <p className="technical-details">Error: {backendError}</p>
              {/* Added onClick for retry button */}
              <button className="retry-button" onClick={onRetry}>Try Again</button>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} aria-hidden="true" />
    </div>
  );
});

const MessageInput = React.memo(({ inputMessage, onInputChange, onSendMessage, isLoading }) => {
  const inputRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      onSendMessage();
    }
  }, [inputMessage, isLoading, onSendMessage]);

  useEffect(() => {
    // Focus input when not loading, but only if it's not already focused
    if (!isLoading && inputRef.current && document.activeElement !== inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  return (
    <form className={`message-input-form ${isFocused ? 'focused' : ''}`} onSubmit={handleSubmit}>
      <div className="input-container">
        <input
          ref={inputRef}
          type="text"
          value={inputMessage}
          onChange={onInputChange}
          placeholder={isLoading ? "Processing your question..." : "Ask about Nepali tax laws..."}
          className="message-input-form__text-input"
          aria-label="Tax question input"
          disabled={isLoading}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          enterKeyHint="send"
        />
        <button
          type="submit"
          className="message-input-form__send-button"
          disabled={!inputMessage.trim() || isLoading}
          aria-label="Send message"
        >
          <SendIcon />
        </button>
      </div>
      <div className="input-hint">
        <span>Press Enter to send</span>
        <span className="hint-divider">•</span>
        <span>Shift+Enter for new line</span>
      </div>
    </form>
  );
});

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [username] = useState('You');
  const [isLoading, setIsLoading] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  const backendUrl = import.meta.env.VITE_BACKEND_URL;

  const [lastQuery, setLastQuery] = useState('');

  const handleSendMessage = useCallback(async (queryToSend = inputMessage) => {
    if ((queryToSend.trim() || lastQuery.trim()) && !isLoading) {
      setBackendError(null);
      setIsLoading(true);
      const messageText = queryToSend.trim() || lastQuery.trim();
      const userMessage = {
        id: Date.now(),
        user: username,
        text: messageText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        type: 'user'
      };
      if (queryToSend.trim() === inputMessage.trim() && !lastQuery.trim()) {
        setMessages(prev => [...prev, userMessage]);
      } else if (lastQuery.trim() && queryToSend.trim() === lastQuery.trim()) {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.type === 'error') {
            return prev.slice(0, -1);
          }
          return prev;
        });
      } else {
         setMessages(prev => [...prev, userMessage]);
      }
      setInputMessage('');
      setLastQuery(messageText);
      try {
        const response = await fetch(`${backendUrl}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: messageText }),
          signal: AbortSignal.timeout(15000)
        });
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}: ${response.statusText || 'Unknown Error'}`);
        }
        const data = await response.json();
        const botMessage = {
          id: Date.now() + 1,
          user: 'Tax Assistant',
          text: data.response,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          type: 'bot',
          context: data.context || []
        };
        setMessages(prev => [...prev, botMessage]);
        setConnectionStatus('connected');
        setLastQuery('');
      } catch (err) {
        setBackendError(err.message);
        setConnectionStatus('disconnected');
        setMessages(prev => [...prev, {
          id: Date.now(),
          user: 'System',
          text: `Failed to get a response. Error: ${err.message}. Please try again.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          type: 'error'
        }]);
      } finally {
        setIsLoading(false);
      }
    }
  }, [inputMessage, username, isLoading, backendUrl, lastQuery]);

  const handleRetryLastMessage = useCallback(() => {
    if (lastQuery) {
      setMessages(prev => prev.filter(msg => msg.type !== 'error'));
      handleSendMessage(lastQuery);
    }
  }, [lastQuery, handleSendMessage]);


  useEffect(() => {
    let timer;
    if (connectionStatus === 'disconnected') {
      timer = setTimeout(() => {
        setConnectionStatus('reconnecting');
      }, 5000);
    }
    return () => clearTimeout(timer);
  }, [connectionStatus]);

  return (
    <ChatLayout>
      <ChatHeader />
      <div className="chat-main-area">
        <DisclaimerBox />
        <MessageList
          messages={messages}
          currentUser={username}
          isLoading={isLoading}
          backendError={backendError}
          onRetry={handleRetryLastMessage} // Pass retry handler
        />
        <MessageInput
          inputMessage={inputMessage}
          onInputChange={(e) => setInputMessage(e.target.value)}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
      <div className={`connection-status ${connectionStatus}`}>
        {connectionStatus === 'connected' ? 'Online' : 
          connectionStatus === 'disconnected' ? 'Offline - Trying to reconnect...' : 'Reconnecting...'}
      </div>
    </ChatLayout>
  );
}

export default App;