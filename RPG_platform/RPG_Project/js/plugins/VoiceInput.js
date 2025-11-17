//=============================================================================
// VoiceInput.js
//=============================================================================

/*:
 * @plugindesc 語音輸入插件 - 支持廣東話語音識別
 * @author AI Assistant
 *
 * @help
 * 這個插件為RPG Maker MV遊戲添加語音輸入功能
 * 
 * 使用方法：
 * 1. 在需要文字輸入的地方調用腳本命令
 * 2. 啟動語音識別
 * 3. 用戶說話後自動填入文字
 * 
 * 腳本命令示例：
 * VoiceInput.start();  // 開始語音識別
 * 
 * 注意：
 * - 需要HTTPS環境或localhost
 * - 僅支持Chrome/Edge瀏覽器
 * - 需要網絡連接Google服務
 */

(function() {
    'use strict';

    //=========================================================================
    // VoiceInput - 核心類
    //=========================================================================
    
    window.VoiceInput = {
        recognition: null,
        isRecording: false,
        callback: null,
        
        // 初始化語音識別
        initialize: function() {
            if (!this.isSupported()) {
                console.warn('[VoiceInput] 瀏覽器不支持語音識別');
                return false;
            }
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // 設置為廣東話
            this.recognition.lang = 'zh-HK';
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 1;
            
            // 綁定事件
            this.setupEvents();
            
            console.log('[VoiceInput] 語音識別已初始化');
            return true;
        },
        
        // 檢查支持
        isSupported: function() {
            return ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);
        },
        
        // 設置事件處理
        setupEvents: function() {
            const self = this;
            
            this.recognition.onstart = function() {
                self.isRecording = true;
                console.log('[VoiceInput] 開始錄音');
                self.showRecordingIndicator();
            };
            
            this.recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                console.log('[VoiceInput] 識別結果:', transcript);
                
                if (self.callback) {
                    self.callback(transcript);
                }
                
                self.hideRecordingIndicator();
            };
            
            this.recognition.onerror = function(event) {
                console.error('[VoiceInput] 錯誤:', event.error);
                self.isRecording = false;
                self.hideRecordingIndicator();
                
                let errorMsg = '';
                switch(event.error) {
                    case 'network':
                        errorMsg = '網絡連接失敗\n請檢查網絡或使用鍵盤輸入';
                        break;
                    case 'not-allowed':
                        errorMsg = '麥克風權限被拒絕\n請在瀏覽器設置中允許';
                        break;
                    case 'no-speech':
                        errorMsg = '未檢測到語音\n請重試或使用鍵盤輸入';
                        break;
                    default:
                        errorMsg = '語音識別失敗: ' + event.error;
                }
                
                self.showError(errorMsg);
            };
            
            this.recognition.onend = function() {
                self.isRecording = false;
                self.hideRecordingIndicator();
                console.log('[VoiceInput] 錄音結束');
            };
        },
        
        // 開始語音識別
        start: function(callback) {
            if (!this.recognition) {
                if (!this.initialize()) {
                    this.showError('您的瀏覽器不支持語音識別\n請使用Chrome或Edge');
                    return false;
                }
            }
            
            // 檢查網絡
            if (!navigator.onLine) {
                this.showError('網絡離線\n語音識別需要網絡連接\n請使用鍵盤輸入');
                return false;
            }
            
            this.callback = callback;
            
            try {
                this.recognition.start();
                return true;
            } catch (error) {
                console.error('[VoiceInput] 啟動失敗:', error);
                this.showError('啟動失敗\n請重試或使用鍵盤輸入');
                return false;
            }
        },
        
        // 停止語音識別
        stop: function() {
            if (this.recognition && this.isRecording) {
                this.recognition.stop();
            }
        },
        
        // 顯示錄音指示器
        showRecordingIndicator: function() {
            // 在遊戲畫面上顯示錄音圖標
            if (SceneManager._scene) {
                const scene = SceneManager._scene;
                
                // 創建錄音指示精靈
                if (!scene._voiceIndicator) {
                    scene._voiceIndicator = new Sprite();
                    scene._voiceIndicator.bitmap = new Bitmap(200, 60);
                    scene._voiceIndicator.x = Graphics.width / 2 - 100;
                    scene._voiceIndicator.y = 20;
                    scene.addChild(scene._voiceIndicator);
                }
                
                const bitmap = scene._voiceIndicator.bitmap;
                bitmap.clear();
                bitmap.fillRect(0, 0, 200, 60, 'rgba(255, 0, 0, 0.8)');
                bitmap.drawText('🎤 錄音中...', 0, 10, 200, 40, 'center');
            }
        },
        
        // 隱藏錄音指示器
        hideRecordingIndicator: function() {
            if (SceneManager._scene && SceneManager._scene._voiceIndicator) {
                const indicator = SceneManager._scene._voiceIndicator;
                SceneManager._scene.removeChild(indicator);
                SceneManager._scene._voiceIndicator = null;
            }
        },
        
        // 顯示錯誤
        showError: function(message) {
            console.error('[VoiceInput]', message);
            
            // 使用遊戲內對話框顯示錯誤
            if ($gameMessage && !$gameMessage.isBusy()) {
                $gameMessage.add(message);
            }
        }
    };
    
    //=========================================================================
    // Window_NameInput - 擴展名字輸入窗口
    //=========================================================================
    
    const _Window_NameInput_initialize = Window_NameInput.prototype.initialize;
    Window_NameInput.prototype.initialize = function(editWindow, maxLength) {
        _Window_NameInput_initialize.call(this, editWindow, maxLength);
        this.createVoiceButton();
    };
    
    // 創建語音按鈕
    Window_NameInput.prototype.createVoiceButton = function() {
        if (!VoiceInput.isSupported()) {
            return;
        }
        
        // 添加語音輸入選項到字符表
        // 可以在這裡自定義語音按鈕的位置
    };
    
    // 處理語音輸入
    Window_NameInput.prototype.processVoiceInput = function() {
        const self = this;
        
        VoiceInput.start(function(transcript) {
            // 將識別的文字填入編輯窗口
            if (self._editWindow) {
                const text = transcript.substring(0, self._maxLength);
                self._editWindow.setName(text);
                self._editWindow.refresh();
            }
        });
    };
    
    //=========================================================================
    // Scene_Name - 擴展名字輸入場景
    //=========================================================================
    
    const _Scene_Name_create = Scene_Name.prototype.create;
    Scene_Name.prototype.create = function() {
        _Scene_Name_create.call(this);
        this.createVoiceButton();
    };
    
    // 創建語音按鈕
    Scene_Name.prototype.createVoiceButton = function() {
        if (!VoiceInput.isSupported()) {
            return;
        }
        
        // 創建語音輸入按鈕
        this._voiceButton = new Sprite_Button();
        this._voiceButton.bitmap = ImageManager.loadSystem('ButtonSet');
        this._voiceButton.setColdFrame(0, 0, 48, 48);
        this._voiceButton.setHotFrame(48, 0, 48, 48);
        this._voiceButton.setClickHandler(this.onVoiceButtonClick.bind(this));
        this._voiceButton.x = Graphics.width - 60;
        this._voiceButton.y = 10;
        this.addChild(this._voiceButton);
    };
    
    // 語音按鈕點擊
    Scene_Name.prototype.onVoiceButtonClick = function() {
        SoundManager.playOk();
        this._inputWindow.processVoiceInput();
    };
    
    //=========================================================================
    // 插件命令
    //=========================================================================
    
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'VoiceInput') {
            switch (args[0]) {
                case 'start':
                    VoiceInput.start(function(transcript) {
                        // 將結果存儲到變量
                        const variableId = parseInt(args[1]) || 1;
                        $gameVariables.setValue(variableId, transcript);
                    });
                    break;
                    
                case 'stop':
                    VoiceInput.stop();
                    break;
                    
                case 'check':
                    const supported = VoiceInput.isSupported();
                    const switchId = parseInt(args[1]) || 1;
                    $gameSwitches.setValue(switchId, supported);
                    break;
            }
        }
    };
    
})();
