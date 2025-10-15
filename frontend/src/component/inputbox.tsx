import React, { useState } from 'react';
import { useTheme } from '../App';

interface InputboxProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const Inputbox: React.FC<InputboxProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
    const { } = useTheme();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="inputbox" onSubmit={handleSubmit}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Enter a company name, website, or suspicious message..."
        disabled={isLoading}
        className="message-input"
      />
      <button 
        type="submit" 
        disabled={isLoading || !input.trim()}
        className="send-button"
      >
        {isLoading ? 'Analyzing...' : 'Send'}
      </button>
    </form>
  );
};

export default Inputbox;

