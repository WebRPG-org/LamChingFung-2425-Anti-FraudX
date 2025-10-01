import React from 'react';
import Message from './message';
import type { MessageProps } from './message';

interface ChatboxProps {
    messages: MessageProps[];
}

const Chatbox: React.FC<ChatboxProps> = ({ messages }) => {
    return (
        <div className="chatbox">
            {messages.map((msg, index) => (
                <Message key={index} text={msg.text} sender={msg.sender} />
            ))}
        </div>
    );
};

export default Chatbox;

