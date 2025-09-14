import React, { useState } from 'react';

interface inputboxProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const inputbox: React.FC<inputboxProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };


    return (
        <form className="inputbox" onSubmit={handleSubmit}>
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !input.trim()}>
                {isLoading ? 'Sending...' : 'Send'}
            </button>
        </form>
    );
};
export default inputbox;