import React from 'react';

export interface messageprops {
    text: string;
    sender: 'user' | 'genai';
}

const message: React.FC<messageprops> = ({ text, sender }) => {
    const messageclass = sender === 'user' ? 'message user-message' : 'message genai-message';
    return (
        <div className={messageclass}>
            <div className="message-bubble">{text}</div>
        </div>
    );
};

export default message;