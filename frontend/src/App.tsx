import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Chatbox from './component/chatbox';
import Inputbox from './component/inputbox';
import type { messageprops } from './component/message';
import './App.css';


const API_URL = 'http://127.0.0.1:8000/api/v1/chat';

function App() {
  const [messages, setMessages] = useState<messageprops[]>([
    { text: '您好！我是香港交通助手，請問想查詢什麼路線？?', sender: 'genai' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatboxRef = useRef<HTMLDivElement>(null);

  //when messages update, auto scroll to bottom
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (query: string) => {
    //show user message
    const userMessage: messageprops = { text: query, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setIsLoading(true);

    try {
      //sent request to backend API
      const response = await axios.post(API_URL, { query });
      
      //show AI response
  const aiMessage: messageprops = { text: response.data.response, sender: 'genai' };
      setMessages(prevMessages => [...prevMessages, aiMessage]);

    } catch (error) {
      console.error("API 請求出錯:", error);
  const errorMessage: messageprops = { text: '抱歉，系統暫時無法連線，請稍後再試。', sender: 'genai' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>香港交通 AI 助手</h1>
      </div>
      <div className="message-list-container" ref={chatboxRef}>
  <Chatbox messages={messages} />
      </div>
  <Inputbox onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}

export default App;