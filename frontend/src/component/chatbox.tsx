import React from 'react';
import Message from './message';
import type { MessageProps } from './message';
import { useTheme } from '../App';

interface ChatboxProps {
    messages: MessageProps[];
}

const Chatbox: React.FC<ChatboxProps> = ({ messages }) => {
    const { isDarkMode } = useTheme();
    
    return (
        <div className="chatbox">
            {messages.map((msg, index) => (
                <Message key={index} text={msg.text} sender={msg.sender} />
            ))}
        </div>
    );
};

export default Chatbox;

