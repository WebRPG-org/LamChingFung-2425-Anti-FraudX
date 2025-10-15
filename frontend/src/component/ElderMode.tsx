import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Eye, EyeOff, Settings, Copy, Check } from 'lucide-react';
import './ElderMode.css';

interface ElderModeProps {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
  onSettingsChange: (settings: ElderModeSettings) => void;
  safetySuggestions: string[];
  aiResponse: string;
}

interface ElderModeSettings {
  enabled: boolean;
  voiceEnabled: boolean;
  largeText: boolean;
  highContrast: boolean;
  simplifiedUI: boolean;
}

const ElderMode: React.FC<ElderModeProps> = ({
  isEnabled,
  onToggle,
  onSettingsChange,
  safetySuggestions,
  aiResponse
}) => {
  const [settings, setSettings] = useState<ElderModeSettings>({
    enabled: isEnabled,
    voiceEnabled: true,
    largeText: true,
    highContrast: true,
    simplifiedUI: true
  });

  const [showSettings, setShowSettings] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    onSettingsChange(settings);
  }, [settings, onSettingsChange]);

  const handleSettingChange = (key: keyof ElderModeSettings, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const speakText = (text: string) => {
    if (!settings.voiceEnabled || !('speechSynthesis' in window)) return;

    // Stop any current speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-TW'; // Traditional Chinese
    utterance.rate = 0.8; // Slower speech for elders
    utterance.pitch = 1.0;
    utterance.volume = 0.9;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleToggle = () => {
    const newEnabled = !isEnabled;
    onToggle(newEnabled);
    setSettings(prev => ({ ...prev, enabled: newEnabled }));
  };

  return (
    <div className={`elder-mode ${isEnabled ? 'enabled' : 'disabled'}`}>
      <div className="elder-mode-header">
        <div className="elder-mode-toggle">
          <button
            className={`toggle-switch ${isEnabled ? 'active' : ''}`}
            onClick={handleToggle}
            aria-label={isEnabled ? '關閉長者模式' : '開啟長者模式'}
          >
            <div className="toggle-track">
              <div className="toggle-thumb">
                {isEnabled ? '👴' : '👶'}
              </div>
            </div>
          </button>
          <div className="toggle-label">
            <h3>長者模式</h3>
            <p>{isEnabled ? '已啟用 - 提供更友善的使用體驗' : '已關閉'}</p>
          </div>
        </div>
        
        <button
          className="settings-btn"
          onClick={() => setShowSettings(!showSettings)}
          title="設定"
        >
          <Settings size={20} />
        </button>
      </div>

      {showSettings && (
        <div className="elder-settings">
          <h4>長者模式設定</h4>
          <div className="settings-grid">
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.voiceEnabled}
                  onChange={(e) => handleSettingChange('voiceEnabled', e.target.checked)}
                />
                <span className="setting-label">
                  <Volume2 size={16} />
                  語音播報
                </span>
              </label>
            </div>
            
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.largeText}
                  onChange={(e) => handleSettingChange('largeText', e.target.checked)}
                />
                <span className="setting-label">
                  <Eye size={16} />
                  大字體
                </span>
              </label>
            </div>
            
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.highContrast}
                  onChange={(e) => handleSettingChange('highContrast', e.target.checked)}
                />
                <span className="setting-label">
                  <EyeOff size={16} />
                  高對比度
                </span>
              </label>
            </div>
            
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.simplifiedUI}
                  onChange={(e) => handleSettingChange('simplifiedUI', e.target.checked)}
                />
                <span className="setting-label">
                  <Settings size={16} />
                  簡化介面
                </span>
              </label>
            </div>
          </div>
        </div>
      )}

      {isEnabled && aiResponse && (
        <div className="elder-response">
          <div className="response-header">
            <h4>AI 分析結果</h4>
            <div className="response-controls">
              <button
                className="voice-btn"
                onClick={() => isSpeaking ? stopSpeaking() : speakText(aiResponse)}
                title={isSpeaking ? '停止語音' : '播放語音'}
              >
                {isSpeaking ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
            </div>
          </div>
          
          <div className={`response-text ${settings.largeText ? 'large-text' : ''}`}>
            {aiResponse}
          </div>
        </div>
      )}

      {isEnabled && safetySuggestions.length > 0 && (
        <div className="safety-suggestions">
          <h4>安全建議</h4>
          <div className="suggestions-grid">
            {safetySuggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-card">
                <div className="suggestion-content">
                  <span className="suggestion-text">{suggestion}</span>
                </div>
                <button
                  className="copy-btn"
                  onClick={() => copyToClipboard(suggestion, index)}
                  title="複製到剪貼簿"
                >
                  {copiedIndex === index ? (
                    <Check size={16} className="copied" />
                  ) : (
                    <Copy size={16} />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ElderMode;

