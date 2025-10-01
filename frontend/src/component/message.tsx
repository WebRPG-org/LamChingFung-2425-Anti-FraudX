import React from 'react';

export interface MessageProps {
    text: string;
    sender: 'user' | 'genai';
}

const Message: React.FC<MessageProps> = ({ text, sender }) => {
    const messageclass = sender === 'user' ? 'message user-message' : 'message genai-message';
    return (
        <div className={messageclass}>
            <div className="message-bubble">{text}</div>
        </div>
    );
};

export default Message;

