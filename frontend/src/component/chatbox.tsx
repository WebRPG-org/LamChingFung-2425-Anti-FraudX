import React from 'react';
import Message from './message';
import type { messageprops } from './message';

interface chatboxprops {
    messages: messageprops[];
}

const chatbox: React.FC<chatboxprops> = ({ messages }) => {
    return (
        <div className="chatbox">
            {messages.map((msg, index) => (
                <Message key={index} text={msg.text} sender={msg.sender} />
            ))}
        </div>
    );
};
export default chatbox;
