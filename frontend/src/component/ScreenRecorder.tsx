import React, { useState, useRef, useEffect } from 'react';
import { Camera, Square, Play, Upload, AlertCircle } from 'lucide-react';
import './ScreenRecorder.css';

interface ScreenRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
  isElderMode?: boolean;
}

const ScreenRecorder: React.FC<ScreenRecorderProps> = ({ 
  onRecordingComplete, 
  isElderMode = false 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [, setRecordedChunks] = useState<Blob[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [showIOSInstructions, setShowIOSInstructions] = useState(false);
  
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Detect iOS
    const userAgent = navigator.userAgent;
    const isIOSDevice = /iPad|iPhone|iPod/.test(userAgent);
    setIsIOS(isIOSDevice);
  }, []);

  useEffect(() => {
    if (isRecording && !isPaused) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, isPaused]);

  const startRecording = async () => {
    try {
      // Check for iOS and show instructions
      if (isIOS) {
        setShowIOSInstructions(true);
        return;
      }

      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: true
      });

      streamRef.current = stream;
      
      const recorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9'
      });

      const chunks: Blob[] = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        setRecordedChunks(chunks);
        setPreviewUrl(URL.createObjectURL(blob));
        onRecordingComplete(blob);
      };

      recorder.start(1000); // Collect data every second
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('無法開始錄影，請檢查瀏覽器權限設定');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  const pauseRecording = () => {
    if (mediaRecorder && isRecording) {
      if (isPaused) {
        mediaRecorder.resume();
        setIsPaused(false);
      } else {
        mediaRecorder.pause();
        setIsPaused(true);
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onRecordingComplete(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  return (
    <div className={`screen-recorder ${isElderMode ? 'elder-mode' : ''}`}>
      <div className="recorder-header">
        <h3>螢幕錄影功能</h3>
        {isIOS && (
          <div className="ios-notice">
            <AlertCircle size={20} />
            <span>iOS 設備需要手動錄影</span>
          </div>
        )}
      </div>

      {showIOSInstructions ? (
        <div className="ios-instructions">
          <h4>iOS 錄影教學</h4>
          <div className="instruction-steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <strong>開始錄影</strong>
                <p>同時按下「電源鍵」和「音量上鍵」開始錄影</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <strong>停止錄影</strong>
                <p>再次按下「電源鍵」和「音量上鍵」停止錄影</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <strong>上傳影片</strong>
                <p>錄影完成後，選擇下方「選擇檔案」上傳影片</p>
              </div>
            </div>
          </div>
          <button 
            className="close-instructions"
            onClick={() => setShowIOSInstructions(false)}
          >
            關閉教學
          </button>
        </div>
      ) : (
        <div className="recorder-controls">
          {!isRecording ? (
            <button 
              className="start-btn"
              onClick={startRecording}
              disabled={isIOS}
            >
              <Camera size={24} />
              {isIOS ? 'iOS 需要手動錄影' : '開始錄影'}
            </button>
          ) : (
            <div className="recording-controls">
              <div className="recording-info">
                <div className="recording-indicator">
                  <div className="pulse"></div>
                  <span>錄影中 {formatTime(recordingTime)}</span>
                </div>
              </div>
              <div className="control-buttons">
                <button 
                  className="pause-btn"
                  onClick={pauseRecording}
                >
                  {isPaused ? <Play size={20} /> : <Square size={20} />}
                  {isPaused ? '繼續' : '暫停'}
                </button>
                <button 
                  className="stop-btn"
                  onClick={stopRecording}
                >
                  <Square size={20} />
                  停止錄影
                </button>
              </div>
            </div>
          )}

          <div className="upload-section">
            <div className="upload-divider">
              <span>或</span>
            </div>
            <label className="upload-btn">
              <Upload size={20} />
              選擇已錄製的影片
              <input
                type="file"
                accept="video/*"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>
      )}

      {previewUrl && (
        <div className="preview-section">
          <h4>影片預覽</h4>
          <video 
            src={previewUrl} 
            controls 
            className="preview-video"
          />
          <div className="preview-actions">
            <button 
              className="upload-btn"
              onClick={() => {
                const link = document.createElement('a');
                link.href = previewUrl;
                link.download = `screen-recording-${Date.now()}.webm`;
                link.click();
              }}
            >
              下載影片
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScreenRecorder;

