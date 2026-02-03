import Phaser from 'phaser';
import { Role } from '../systems/RoleManager';

interface BattleSceneData {
  npcType: string;
  npcName: string;
  playerRole: Role;
}

export class BattleScene extends Phaser.Scene {
  private data!: BattleSceneData;
  private messages: Array<{ speaker: string; text: string; color: string }> = [];
  private messageContainer!: Phaser.GameObjects.Container;
  private inputField!: HTMLInputElement;

  constructor() {
    super({ key: 'BattleScene' });
  }

  init(data: BattleSceneData): void {
    this.data = data;
    this.messages = [];
  }

  create(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Background
    this.add.rectangle(0, 0, width, height, 0x1A1F2E).setOrigin(0, 0);

    // Header
    this.createHeader();

    // Message area
    this.createMessageArea();

    // Input area
    this.createInputArea();

    // Initial message
    this.addSystemMessage(`對話開始：${this.data.npcName}`);
    this.addSystemMessage(`你的角色：${this.data.playerRole.nameZh}`);
    this.addSystemMessage('輸入訊息開始對話...');
  }

  private createHeader(): void {
    const width = this.cameras.main.width;

    const header = this.add.container(0, 0);
    
    const bg = this.add.rectangle(0, 0, width, 80, 0x2D3748).setOrigin(0, 0);
    
    const backButton = this.add.text(20, 25, '← 返回', {
      fontSize: '18px',
      color: '#ffffff',
      backgroundColor: '#6C5CE7',
      padding: { x: 15, y: 8 }
    });
    backButton.setInteractive({ useHandCursor: true });
    backButton.on('pointerdown', () => this.returnToWorld());
    backButton.on('pointerover', () => backButton.setScale(1.05));
    backButton.on('pointerout', () => backButton.setScale(1));

    const title = this.add.text(width / 2, 40, `對話：${this.data.npcName}`, {
      fontSize: '24px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    const roleText = this.add.text(width - 20, 40, 
      `${this.data.playerRole.icon} ${this.data.playerRole.nameZh}`, {
      fontSize: '16px',
      color: this.data.playerRole.color,
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });
    roleText.setOrigin(1, 0.5);

    header.add([bg, backButton, title, roleText]);
  }

  private createMessageArea(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Message container background
    const messageBg = this.add.rectangle(
      width / 2, 
      height / 2 - 20, 
      width - 40, 
      height - 240, 
      0x2D3748
    );

    // Scrollable message container
    this.messageContainer = this.add.container(20, 100);
  }

  private createInputArea(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const inputBg = this.add.rectangle(
      width / 2,
      height - 60,
      width - 40,
      80,
      0x2D3748
    );

    // Create HTML input field
    this.inputField = document.createElement('input');
    this.inputField.type = 'text';
    this.inputField.placeholder = '輸入你的回應...';
    this.inputField.style.position = 'absolute';
    this.inputField.style.left = '40px';
    this.inputField.style.bottom = '40px';
    this.inputField.style.width = `${width - 180}px`;
    this.inputField.style.height = '40px';
    this.inputField.style.fontSize = '16px';
    this.inputField.style.padding = '10px';
    this.inputField.style.backgroundColor = '#1A1F2E';
    this.inputField.style.color = '#ffffff';
    this.inputField.style.border = '2px solid #6C5CE7';
    this.inputField.style.borderRadius = '8px';
    this.inputField.style.outline = 'none';

    document.body.appendChild(this.inputField);

    // Send button
    const sendButton = this.add.text(width - 80, height - 60, '發送', {
      fontSize: '16px',
      color: '#ffffff',
      backgroundColor: '#6C5CE7',
      padding: { x: 20, y: 10 }
    });
    sendButton.setOrigin(0.5);
    sendButton.setInteractive({ useHandCursor: true });
    sendButton.on('pointerdown', () => this.sendMessage());
    sendButton.on('pointerover', () => sendButton.setScale(1.05));
    sendButton.on('pointerout', () => sendButton.setScale(1));

    // Enter key to send
    this.inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage();
      }
    });

    this.inputField.focus();
  }

  private sendMessage(): void {
    const message = this.inputField.value.trim();
    
    if (message) {
      this.addMessage(
        this.data.playerRole.nameZh,
        message,
        this.data.playerRole.color
      );
      
      this.inputField.value = '';
      
      // Simulate AI response (placeholder)
      this.time.delayedCall(1000, () => {
        this.addAIResponse();
      });
    }
  }

  private addMessage(speaker: string, text: string, color: string): void {
    this.messages.push({ speaker, text, color });
    this.renderMessages();
  }

  private addSystemMessage(text: string): void {
    this.addMessage('系統', text, '#FDCB6E');
  }

  private addAIResponse(): void {
    // Placeholder AI responses
    const responses = [
      '我明白你的意思...',
      '這聽起來很有趣',
      '讓我想想...',
      '你說得對',
      '我需要更多資訊'
    ];
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    this.addMessage(this.data.npcName, randomResponse, '#00B894');
  }

  private renderMessages(): void {
    this.messageContainer.removeAll(true);

    const startY = 0;
    const messageSpacing = 80;
    const maxMessages = 6;
    
    // Show only last N messages
    const visibleMessages = this.messages.slice(-maxMessages);

    visibleMessages.forEach((msg, index) => {
      const y = startY + index * messageSpacing;
      
      const speakerText = this.add.text(0, y, msg.speaker, {
        fontSize: '14px',
        color: msg.color,
        fontStyle: 'bold'
      });

      const messageText = this.add.text(0, y + 20, msg.text, {
        fontSize: '16px',
        color: '#ffffff',
        wordWrap: { width: this.cameras.main.width - 80 }
      });

      this.messageContainer.add([speakerText, messageText]);
    });
  }

  private returnToWorld(): void {
    // Clean up HTML input
    if (this.inputField && this.inputField.parentNode) {
      this.inputField.parentNode.removeChild(this.inputField);
    }
    
    this.scene.start('WorldMapScene');
  }

  shutdown(): void {
    // Clean up HTML input when scene shuts down
    if (this.inputField && this.inputField.parentNode) {
      this.inputField.parentNode.removeChild(this.inputField);
    }
  }
}
