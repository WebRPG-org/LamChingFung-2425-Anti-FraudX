import React, { useState } from 'react';

interface InputboxProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const Inputbox: React.FC<InputboxProps> = ({ onSendMessage, isLoading }) => {
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
        placeholder="輸入公司、網址或可疑訊息..."
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading || !input.trim()}>
        {isLoading ? '分析中...' : '查詢'}
      </button>
    </form>
  );
};

export default Inputbox;

