const API_BASE_URL = 'http://localhost:8000';
let currentSessionId = null;
let currentMode = null;
let selectedImages = []; // 儲存選中的圖片

// 模式選擇
document.querySelectorAll('.mode-button').forEach(button => {
    button.addEventListener('click', function() {
        // 移除其他按鈕的選中狀態
        document.querySelectorAll('.mode-button').forEach(b => b.classList.remove('selected'));
        // 添加當前按鈕的選中狀態
        this.classList.add('selected');
        
        currentMode = this.dataset.mode;
        document.getElementById('startButton').disabled = false;
        
        // 如果是騙徒模式，顯示騙局選擇器
        const scamTypeSelector = document.getElementById('scamTypeSelector');
        if (currentMode === 'scammer') {
            scamTypeSelector.classList.add('show');
        } else {
            scamTypeSelector.classList.remove('show');
        }
    });
});

// 開始對話
document.getElementById('startButton').addEventListener('click', async function() {
    if (!currentMode) return;
    
    this.disabled = true;
    this.textContent = '正在啟動...';
    
    try {
        const requestBody = {
            mode: currentMode
        };
        
        if (currentMode === 'scammer') {
            requestBody.scam_type = document.getElementById('scamType').value;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/personal-chat/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = data.session_id;
            
            // 隱藏模式選擇，顯示聊天界面
            document.getElementById('modeSelection').style.display = 'none';
            document.getElementById('chatContainer').classList.add('active');
            
            // 更新頭部顯示
            const modeIndicator = document.getElementById('modeIndicator');
            const modeIcon = document.getElementById('modeIcon');
            const modeName = document.getElementById('modeName');
            
            modeIndicator.style.display = 'flex';
            if (currentMode === 'assistant') {
                modeIcon.textContent = '🛡️';
                modeName.textContent = '防詐助手';
            } else {
                modeIcon.textContent = '🎭';
                modeName.textContent = '騙徒模擬';
            }
            
            // 顯示歡迎消息
            addMessage(data.reply, currentMode);
            
            // 自動播放歡迎語音
            speakText(data.reply);
            
            // 聚焦輸入框
            document.getElementById('messageInput').focus();
        }
    } catch (error) {
        console.error('啟動對話失敗:', error);
        alert('啟動對話失敗，請檢查後端服務是否運行');
        this.disabled = false;
        this.textContent = '開始對話';
    }
});

// 處理圖片選擇
function handleImageSelect(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    for (let file of files) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                selectedImages.push({
                    file: file,
                    dataUrl: e.target.result
                });
                updateImagePreview();
            };
            reader.readAsDataURL(file);
        }
    }
    
    // 清空 input，允許重複選擇同一文件
    event.target.value = '';
}

// 更新圖片預覽
function updateImagePreview() {
    const container = document.getElementById('imagePreviewContainer');
    container.innerHTML = '';
    
    if (selectedImages.length === 0) {
        container.classList.remove('show');
        return;
    }
    
    container.classList.add('show');
    
    selectedImages.forEach((img, index) => {
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${img.dataUrl}" alt="預覽" />
            <button class="remove-image" onclick="removeImage(${index})">×</button>
        `;
        container.appendChild(preview);
    });
}

// 移除圖片
function removeImage(index) {
    selectedImages.splice(index, 1);
    updateImagePreview();
}

// 打開圖片燈箱
function openLightbox(imageSrc) {
    const lightbox = document.getElementById('imageLightbox');
    const lightboxImage = document.getElementById('lightboxImage');
    lightboxImage.src = imageSrc;
    lightbox.classList.add('show');
}

// 關閉圖片燈箱
function closeLightbox() {
    const lightbox = document.getElementById('imageLightbox');
    lightbox.classList.remove('show');
}

// 發送消息
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    // 至少要有文字或圖片
    if ((!message && selectedImages.length === 0) || !currentSessionId) return;
    
    // 清空輸入框並禁用
    input.value = '';
    input.disabled = true;
    document.getElementById('sendButton').disabled = true;
    
    // 準備 FormData
    const formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('message', message || '');
    
    // 添加圖片
    selectedImages.forEach((img, index) => {
        formData.append('images', img.file);
    });
    
    // 顯示用戶消息（包含圖片）
    addMessageWithImages(message, selectedImages.map(img => img.dataUrl), 'user');
    
    // 清空已選圖片
    selectedImages = [];
    updateImagePreview();
    
    // 顯示加載動畫
    document.getElementById('loading').classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/personal-chat/message`, {
            method: 'POST',
            body: formData  // 使用 FormData 而不是 JSON
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 隱藏加載動畫
            document.getElementById('loading').classList.remove('show');
            
            // 顯示AI回應
            addMessage(data.reply, currentMode);
            
            // 自動播放語音
            speakText(data.reply);
        }
    } catch (error) {
        console.error('發送消息失敗:', error);
        document.getElementById('loading').classList.remove('show');
        addMessage('抱歉，發送消息失敗，請重試', 'system');
    } finally {
        // 重新啟用輸入
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        input.focus();
    }
}

// 添加消息到聊天區域
function addMessage(text, type) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let avatarEmoji = '👤';
    if (type === 'assistant') avatarEmoji = '🛡️';
    else if (type === 'scammer') avatarEmoji = '🎭';
    else if (type === 'user') avatarEmoji = '👤';
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-avatar">${avatarEmoji}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarEmoji}</div>
            <div class="message-content">${text}</div>
        `;
    }
    
    messagesContainer.insertBefore(messageDiv, document.getElementById('loading'));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 添加帶圖片的消息
function addMessageWithImages(text, imageUrls, type) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    let avatarEmoji = '👤';
    if (type === 'assistant') avatarEmoji = '🛡️';
    else if (type === 'scammer') avatarEmoji = '🎭';
    else if (type === 'user') avatarEmoji = '👤';
    
    let imagesHtml = '';
    if (imageUrls && imageUrls.length > 0) {
        imagesHtml = imageUrls.map(url => 
            `<img src="${url}" class="message-image" onclick="openLightbox('${url}')" alt="上傳的圖片" />`
        ).join('');
    }
    
    const contentHtml = text ? `<div>${text}</div>` : '';
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">${contentHtml}${imagesHtml}</div>
            <div class="message-avatar">${avatarEmoji}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarEmoji}</div>
            <div class="message-content">${contentHtml}${imagesHtml}</div>
        `;
    }
    
    messagesContainer.insertBefore(messageDiv, document.getElementById('loading'));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 清除對話
function clearChat() {
    if (confirm('確定要清除所有對話記錄嗎？')) {
        const messagesContainer = document.getElementById('chatMessages');
        const messages = messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
    }
}

// 重新開始
async function restartChat() {
    if (confirm('確定要重新開始嗎？當前對話將結束')) {
        if (currentSessionId) {
            try {
                await fetch(`${API_BASE_URL}/api/personal-chat/session/${currentSessionId}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                console.error('結束會話失敗:', error);
            }
        }
        
        // 重置狀態
        currentSessionId = null;
        currentMode = null;
        
        // 清除消息
        const messagesContainer = document.getElementById('chatMessages');
        const messages = messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        // 返回模式選擇
        document.getElementById('chatContainer').classList.remove('active');
        document.getElementById('modeSelection').style.display = 'block';
        document.getElementById('modeIndicator').style.display = 'none';
        document.getElementById('startButton').disabled = true;
        document.getElementById('startButton').textContent = '開始對話';
        
        // 清除模式選擇
        document.querySelectorAll('.mode-button').forEach(b => b.classList.remove('selected'));
        document.getElementById('scamTypeSelector').classList.remove('show');
    }
}

// 匯出對話
function exportChat() {
    const messages = document.querySelectorAll('.message');
    let exportText = `AI 防詐騙對話記錄\n`;
    exportText += `模式：${currentMode === 'assistant' ? '防詐助手' : '騙徒模擬'}\n`;
    exportText += `時間：${new Date().toLocaleString()}\n`;
    exportText += `${'='.repeat(50)}\n\n`;
    
    messages.forEach(msg => {
        const type = msg.classList.contains('user') ? '用戶' : 
                    msg.classList.contains('assistant') ? '助手' : '騙徒';
        const content = msg.querySelector('.message-content').textContent;
        exportText += `${type}：${content}\n\n`;
    });
    
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// ===== 語音功能 =====
let recognition = null;
let isRecording = false;
let speechSynthesis = window.speechSynthesis;
let silenceTimer = null;
let finalTranscript = '';
const SILENCE_DELAY = 2000; // 2秒停頓緩衝

// 初始化語音識別
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-HK'; // 廣東話
        recognition.continuous = true;  // 改為連續模式
        recognition.interimResults = true;  // 啟用即時結果

        recognition.onresult = function(event) {
            // 清除之前的靜默計時器
            if (silenceTimer) {
                clearTimeout(silenceTimer);
                silenceTimer = null;
            }

            let interimTranscript = '';
            let currentFinalTranscript = '';

            // 處理所有結果
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    currentFinalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            // 更新最終文本
            if (currentFinalTranscript) {
                finalTranscript += currentFinalTranscript;
            }

            // 顯示當前識別的文本（最終 + 臨時）
            const displayText = finalTranscript + interimTranscript;
            document.getElementById('messageInput').value = displayText;
            console.log('語音識別中:', displayText);

            // 設置2秒靜默計時器
            silenceTimer = setTimeout(() => {
                if (recognition && isRecording) {
                    console.log('2秒無語音，自動停止錄音');
                    recognition.stop();
                }
            }, SILENCE_DELAY);
        };

        recognition.onerror = function(event) {
            console.error('語音識別錯誤:', event.error);
            
            // 根據錯誤類型提供不同的提示
            let errorMessage = '';
            let showKeyboardHint = false;
            
            switch(event.error) {
                case 'network':
                    errorMessage = '⚠️ 語音識別暫時不可用\n\n可能原因：\n• 網絡連接問題\n• VPN干擾\n• 防火墻阻止\n\n💡 建議：使用鍵盤輸入（完全可用）';
                    showKeyboardHint = true;
                    break;
                case 'not-allowed':
                    errorMessage = '🎤 麥克風權限被拒絕\n\n請在瀏覽器地址欄左側點擊🔒圖標\n允許「麥克風」權限';
                    break;
                case 'no-speech':
                    errorMessage = '未檢測到語音\n\n請確保：\n• 麥克風正常工作\n• 說話聲音足夠大\n• 環境不要太吵';
                    break;
                case 'audio-capture':
                    errorMessage = '❌ 無法訪問麥克風\n\n請檢查：\n• 麥克風是否連接\n• 其他程序是否占用\n• 設備驅動是否正常';
                    break;
                case 'aborted':
                    console.log('語音識別被用戶中止');
                    stopRecording();
                    return; // 不顯示提示
                default:
                    errorMessage = '語音識別失敗: ' + event.error;
            }
            
            alert(errorMessage);
            stopRecording();
            
            // 對於network錯誤，聚焦輸入框提示用鍵盤
            if (showKeyboardHint) {
                setTimeout(() => {
                    const input = document.getElementById('messageInput');
                    if (input) {
                        input.focus();
                        input.placeholder = '💡 請使用鍵盤輸入（語音暫不可用）';
                    }
                }, 100);
            }
        };

        recognition.onend = function() {
            // 清除靜默計時器
            if (silenceTimer) {
                clearTimeout(silenceTimer);
                silenceTimer = null;
            }
            
            // 確保最終文本已保存
            if (finalTranscript) {
                document.getElementById('messageInput').value = finalTranscript;
                console.log('最終語音識別結果:', finalTranscript);
            }
            
            stopRecording();
        };
    } else {
        console.warn('瀏覽器不支持語音識別');
    }
}

// 切換語音輸入
async function toggleVoiceInput() {
    if (!recognition) {
        alert('您的瀏覽器不支持語音識別功能。請使用Chrome、Edge或Safari瀏覽器。');
        return;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        // 檢查網絡連接
        if (!navigator.onLine) {
            alert('未檢測到網絡連接。語音識別需要網絡連接才能工作。\n請檢查您的網絡設置。');
            return;
        }
        
        try {
            // 重置最終文本
            finalTranscript = '';
            
            recognition.start();
            startRecording();
        } catch (error) {
            console.error('啟動語音識別失敗:', error);
            alert('啟動語音識別失敗。請重試。\n' + error.message);
        }
    }
}

// 開始錄音
function startRecording() {
    isRecording = true;
    const voiceButton = document.getElementById('voiceButton');
    voiceButton.classList.add('recording');
    voiceButton.textContent = '🔴';
    voiceButton.title = '停止錄音';
}

// 停止錄音
function stopRecording() {
    isRecording = false;
    
    // 清除靜默計時器
    if (silenceTimer) {
        clearTimeout(silenceTimer);
        silenceTimer = null;
    }
    
    const voiceButton = document.getElementById('voiceButton');
    voiceButton.classList.remove('recording');
    voiceButton.textContent = '🎤';
    voiceButton.title = '語音輸入';
}

// 文字轉語音
function speakText(text) {
    // 檢查是否啟用自動播放
    const autoSpeak = document.getElementById('autoSpeakToggle').checked;
    if (!autoSpeak) {
        return;
    }

    // 停止當前正在播放的語音
    speechSynthesis.cancel();

    // 創建語音合成實例
    const utterance = new SpeechSynthesisUtterance(text);
    
    // 設置語音參數
    utterance.lang = 'zh-HK'; // 廣東話
    utterance.rate = 1.0; // 語速
    utterance.pitch = 1.0; // 音調
    utterance.volume = 1.0; // 音量

    // 嘗試選擇廣東話語音
    const voices = speechSynthesis.getVoices();
    const cantoneseVoice = voices.find(voice => 
        voice.lang.includes('zh-HK') || 
        voice.lang.includes('yue') ||
        voice.name.includes('Cantonese')
    );
    
    if (cantoneseVoice) {
        utterance.voice = cantoneseVoice;
    }

    // 播放語音
    speechSynthesis.speak(utterance);
    
    console.log('開始播放語音:', text.substring(0, 50) + '...');
}

// 初始化語音功能
window.addEventListener('load', function() {
    initSpeechRecognition();
    
    // 確保語音列表已加載
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = function() {
            console.log('語音列表已加載');
        };
    }
});

// 按Enter發送消息
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
