import { useState, useEffect, useRef, createContext, useContext } from 'react';
import axios from 'axios';
import Chatbox from './component/chatbox'; 
import Inputbox from './component/inputbox'; 
import ScreenRecorder from './component/ScreenRecorder';
import ElderMode from './component/ElderMode';
import type { MessageProps } from './component/message'; 
import './App.css';

// Theme Context
interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// The unified chat endpoint for our backend
const API_URL = 'http://localhost:8000/api/v1/chat';

function App() {
  const [messages, setMessages] = useState<MessageProps[]>([
    { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });
  const [chatHistory, setChatHistory] = useState<Array<{id: string, title: string, date: string, messages: MessageProps[]}>>([
    { 
      id: '1', 
      title: 'Financial Fraud Query', 
      date: '2024-10-04',
      messages: [
        { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' },
        { text: 'Can you check this company?', sender: 'user' },
        { text: 'I can help you with that. Please provide more details.', sender: 'genai' }
      ]
    },
    { 
      id: '2', 
      title: 'Previous Chat 2', 
      date: '2024-10-03',
      messages: [
        { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' }
      ]
    },
    { 
      id: '3', 
      title: 'Previous Chat 3', 
      date: '2024-10-02',
      messages: [
        { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' }
      ]
    }
  ]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 });
  const [isElderMode, setIsElderMode] = useState(false);
  const [safetySuggestions, setSafetySuggestions] = useState<string[]>([]);
  const [showScreenRecorder, setShowScreenRecorder] = useState(false);
  const [lastAIResponse, setLastAIResponse] = useState<string>('');
  const chatboxRef = useRef<HTMLDivElement>(null);
  const avatarRef = useRef<HTMLDivElement>(null);

  const toggleTheme = () => {
    setIsDarkMode(prev => {
      const newTheme = !prev;
      localStorage.setItem('theme', newTheme ? 'dark' : 'light');
      return newTheme;
    });
  };

  // Create a new chat
  const handleNewChat = () => {
    console.log('=== NEW CHAT CLICKED ===');
    console.log('Current messages:', messages);
    console.log('Messages length:', messages.length);
    console.log('Current chat ID:', currentChatId);
    console.log('Current history count:', chatHistory.length);
    
    const newMessages: MessageProps[] = [
      { text: 'Hello! I am your financial AI assistant. Please enter a company name, website, or suspicious message for inquiry.', sender: 'genai' }
    ];
    
    // Save current chat to history if it has messages beyond the initial greeting
    if (messages.length > 1) {
      console.log('✓ Saving chat (has', messages.length, 'messages)');
      
      if (currentChatId === null) {
        console.log('✓ This is a NEW unsaved chat');
        // Create new chat entry for unsaved chat
        const firstUserMessage = messages.find(m => m.sender === 'user');
        const title = firstUserMessage 
          ? firstUserMessage.text.substring(0, 30) + (firstUserMessage.text.length > 30 ? '...' : '')
          : `New Chat ${Date.now()}`;
        
        const newChat = {
          id: Date.now().toString(),
          title: title,
          date: new Date().toISOString().split('T')[0],
          messages: [...messages]
        };
        
        console.log('✓ Created new chat object:', newChat);
        console.log('✓ Adding to history...');
        
        setChatHistory(prev => {
          const updated = [newChat, ...prev];
          console.log('✓ History updated! New count:', updated.length);
          console.log('✓ First item in history:', updated[0]);
          return updated;
        });
      } else {
        // Update existing chat in history
        console.log('✓ Updating EXISTING chat:', currentChatId);
        setChatHistory(prev => prev.map(c => 
          c.id === currentChatId ? { ...c, messages: [...messages] } : c
        ));
      }
    } else {
      console.log('✗ NOT saving - only', messages.length, 'message(s). Need at least 2.');
    }
    
    // Reset to new chat
    console.log('→ Resetting to new chat with 1 message');
    setMessages(newMessages);
    setCurrentChatId(null);
    console.log('=== NEW CHAT COMPLETE ===\n');
  };

  // Load a chat from history
  const handleLoadChat = (chatId: string) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      // Save current chat before switching
      if (messages.length > 1 && currentChatId === null) {
        const firstUserMessage = messages.find(m => m.sender === 'user');
        const title = firstUserMessage 
          ? firstUserMessage.text.substring(0, 30) + (firstUserMessage.text.length > 30 ? '...' : '')
          : `Chat ${chatHistory.length + 1}`;
        
        const newChat = {
          id: Date.now().toString(),
          title: title,
          date: new Date().toISOString().split('T')[0],
          messages: messages
        };
        setChatHistory(prev => [newChat, ...prev]);
      } else if (currentChatId !== null && currentChatId !== chatId) {
        // Update existing chat
        setChatHistory(prev => prev.map(c => 
          c.id === currentChatId ? { ...c, messages } : c
        ));
      }
      
      setMessages(chat.messages);
      setCurrentChatId(chatId);
    }
  };

  // Delete a chat from history
  const handleDeleteChat = (chatId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the load chat
    setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
    
    // If deleting the current chat, create a new one
    if (currentChatId === chatId) {
      handleNewChat();
    }
  };

  const themeValue = { isDarkMode, toggleTheme };

  // Auto-scroll to the bottom when messages update
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  // Track mouse movement for eye following
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (avatarRef.current) {
        const avatarRect = avatarRef.current.getBoundingClientRect();
        const avatarCenterX = avatarRect.left + avatarRect.width / 2;
        const avatarCenterY = avatarRect.top + avatarRect.height / 2;
        
        const deltaX = e.clientX - avatarCenterX;
        const deltaY = e.clientY - avatarCenterY;
        
        const angle = Math.atan2(deltaY, deltaX);
        const distance = Math.min(Math.sqrt(deltaX * deltaX + deltaY * deltaY) / 100, 1);
        
        const maxMove = 8; // Maximum eye movement in pixels
        const x = Math.cos(angle) * distance * maxMove;
        const y = Math.sin(angle) * distance * maxMove;
        
        setEyePosition({ x, y });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleSendMessage = async (query: string) => {
    // Immediately display the user's message
    const userMessage: MessageProps = { text: query, sender: 'user' };
    setMessages(prevMessages => {
      const newMessages = [...prevMessages, userMessage];
      
      // Auto-save to history if this is a new chat with messages
      if (currentChatId !== null) {
        setChatHistory(prev => prev.map(c => 
          c.id === currentChatId ? { ...c, messages: newMessages, title: query.substring(0, 30) + (query.length > 30 ? '...' : '') } : c
        ));
      }
      
      return newMessages;
    });
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
      setLastAIResponse(response.data.response);
      
      // Extract safety suggestions if available
      if (response.data.safety_suggestions) {
        setSafetySuggestions(response.data.safety_suggestions);
      }
      
      setMessages(prevMessages => {
        const newMessages = [...prevMessages, aiMessage];
        
        // Update history with AI response
        if (currentChatId !== null) {
          setChatHistory(prev => prev.map(c => 
            c.id === currentChatId ? { ...c, messages: newMessages } : c
          ));
        }
        
        return newMessages;
      });

    } catch (error) {
      console.error("API request error:", error);
      const errorMessage: MessageProps = { text: 'Sorry, the system is temporarily unable to connect. Please try again later.', sender: 'genai' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleScreenRecording = async (blob: Blob) => {
    try {
      setIsLoading(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', blob, `screen-recording-${Date.now()}.webm`);
      
      // Upload file to backend
      await axios.post(
        'http://localhost:8000/api/v1/media/upload-video',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      // Add message about video upload
      const uploadMessage: MessageProps = { 
        text: '螢幕錄影已上傳，正在分析中...', 
        sender: 'genai' 
      };
      setMessages(prevMessages => [...prevMessages, uploadMessage]);
      
    } catch (error) {
      console.error("Screen recording upload error:", error);
      const errorMessage: MessageProps = { 
        text: '螢幕錄影上傳失敗，請重試', 
        sender: 'genai' 
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleElderModeToggle = (enabled: boolean) => {
    setIsElderMode(enabled);
    localStorage.setItem('elderMode', enabled.toString());
  };

  const handleElderModeSettingsChange = (settings: any) => {
    // Apply elder mode settings to the app
    if (settings.largeText) {
      document.body.classList.add('elder-large-text');
    } else {
      document.body.classList.remove('elder-large-text');
    }
    
    if (settings.highContrast) {
      document.body.classList.add('elder-high-contrast');
    } else {
      document.body.classList.remove('elder-high-contrast');
    }
    
    if (settings.simplifiedUI) {
      document.body.classList.add('elder-simplified-ui');
    } else {
      document.body.classList.remove('elder-simplified-ui');
    }
  };

  return (
    <ThemeContext.Provider value={themeValue}>
      <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
        {/* History Sidebar */}
        <aside className={`history-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            {isSidebarOpen && <h2>Chat History</h2>}
            <button 
              className="sidebar-toggle" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
            >
              {isSidebarOpen ? '◀' : '▶'}
            </button>
          </div>
          {isSidebarOpen && (
            <div className="history-list">
              <button className="new-chat-btn" onClick={handleNewChat}>+ New Chat</button>
              {chatHistory.map(chat => (
                <div 
                  key={chat.id} 
                  className={`history-item ${currentChatId === chat.id ? 'active' : ''}`}
                  onClick={() => handleLoadChat(chat.id)}
                >
                  <div className="history-item-content">
                    <span className="history-title">{chat.title}</span>
                    <span className="history-date">{chat.date}</span>
                  </div>
                  <button 
                    className="delete-chat-btn" 
                    onClick={(e) => handleDeleteChat(chat.id, e)}
                    title="Delete chat"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Main Chat Container */}
        <div className="chat-container">
          <div className="chat-header">
            <div className="header-content">
              <button 
                className="mobile-sidebar-toggle" 
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              >
                ☰
              </button>
              <h1>Hong Kong Financial AI Assistant</h1>
              <div className="header-controls">
                <button 
                  className={`screen-recorder-toggle ${showScreenRecorder ? 'active' : ''}`}
                  onClick={() => setShowScreenRecorder(!showScreenRecorder)}
                  title="螢幕錄影功能"
                >
                  📹
                </button>
                <button 
                  className={`theme-toggle-switch ${isDarkMode ? 'dark' : 'light'}`} 
                  onClick={toggleTheme} 
                  title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                >
                <div className="toggle-track">
                  {isDarkMode ? (
                    <>
                      <div className="stars">
                        <span className="star" style={{left: '15%', top: '25%'}}>✦</span>
                        <span className="star" style={{left: '35%', top: '60%'}}>✦</span>
                        <span className="star" style={{left: '55%', top: '35%'}}>✦</span>
                        <span className="star" style={{left: '75%', top: '55%'}}>✦</span>
                        <span className="star" style={{left: '25%', top: '70%'}}>✦</span>
                      </div>
                      <div className="toggle-thumb moon"></div>
                    </>
                  ) : (
                    <>
                      <div className="toggle-thumb sun">
                        <div className="cloud"></div>
                      </div>
                    </>
                  )}
                </div>
              </button>
              </div>
            </div>
          </div>
          <div className="message-list-container" ref={chatboxRef}>
            <Chatbox messages={messages} />
          </div>
          
          {/* Elder Mode Component */}
          <ElderMode
            isEnabled={isElderMode}
            onToggle={handleElderModeToggle}
            onSettingsChange={handleElderModeSettingsChange}
            safetySuggestions={safetySuggestions}
            aiResponse={lastAIResponse}
          />
          
          {/* Screen Recorder Component */}
          {showScreenRecorder && (
            <ScreenRecorder
              onRecordingComplete={handleScreenRecording}
              isElderMode={isElderMode}
            />
          )}
          
          <Inputbox onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>

        {/* Virtual Model Box */}
        <aside className="model-sidebar">
          <div className="model-header">
            <h2>Virtual Assistant</h2>
          </div>
          <div className="model-container">
            <div className="model-placeholder">
              <div className="model-avatar-human" ref={avatarRef}>
                <div className="avatar-head">
                  <div className="avatar-hair"></div>
                  <div className="avatar-face">
                    <div className="avatar-eyes">
                      <div 
                        className="eye left" 
                        style={{ transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)` }}
                      ></div>
                      <div 
                        className="eye right" 
                        style={{ transform: `translate(${eyePosition.x}px, ${eyePosition.y}px)` }}
                      ></div>
                    </div>
                    <div className="avatar-mouth"></div>
                  </div>
                </div>
                <div className="avatar-body"></div>
              </div>
              <p className="model-status">{isLoading ? 'Analyzing...' : 'Ready to assist'}</p>
              <div className="model-info">
                <h3>AI Financial Advisor</h3>
                <p>Your intelligent assistant for financial fraud detection and analysis.</p>
              </div>
            </div>
          </div>
          <div className="model-stats">
            <div className="stat-item">
              <span className="stat-label">Messages</span>
              <span className="stat-value">{messages.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Status</span>
              <span className="stat-value">{isLoading ? 'Processing...' : 'Active'}</span>
            </div>
          </div>
        </aside>
      </div>
    </ThemeContext.Provider>
  );
}

export default App;

