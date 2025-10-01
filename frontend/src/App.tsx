import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Chatbox from './component/chatbox'; 
import Inputbox from './component/inputbox'; 
import type { MessageProps } from './component/message'; 
import './App.css';

// The unified chat endpoint for our backend
const API_URL = 'http://localhost:8000/api/v1/chat';

function App() {
  const [messages, setMessages] = useState<MessageProps[]>([
    
    { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatboxRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when messages update
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (query: string) => {
    // Immediately display the user's message
    const userMessage: MessageProps = { text: query, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsLoading(true);

    try {
      // Send request to the backend API with RAG enabled
      const response = await axios.post(API_URL, { 
        query, 
        use_rag: true,
        session_id: `frontend_${Date.now()}`
      });
      
      // Display the AI's response
      const aiMessage: MessageProps = { text: response.data.response, sender: 'genai' };
      setMessages(prevMessages => [...prevMessages, aiMessage]);

    } catch (error) {
      console.error("API request error:", error);
      const errorMessage: MessageProps = { text: 'Sorry, the system is temporarily unable to connect. Please try again later.', sender: 'genai' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Hong Kong Financial AI Assistant</h1>
      </div>
      <div className="message-list-container" ref={chatboxRef}>
        <Chatbox messages={messages} />
      </div>
      <Inputbox onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}

export default App;

