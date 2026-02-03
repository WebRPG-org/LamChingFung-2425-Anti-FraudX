import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { MainMenuScene } from './scenes/MainMenuScene';
import { WorldMapScene } from './scenes/WorldMapScene';
import { BattleScene } from './scenes/BattleScene';
import { AutoModeScene } from './scenes/AutoModeScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 1280,
  height: 720,
  parent: 'game-container',
  backgroundColor: '#1A1F2E',
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { x: 0, y: 0 },
      debug: false
    }
  },
  scene: [
    BootScene,
    MainMenuScene,
    WorldMapScene,
    BattleScene,
    AutoModeScene
  ]
};

// Hide loading screen when game starts
window.addEventListener('load', () => {
  const loading = document.getElementById('loading');
  if (loading) {
    setTimeout(() => {
      loading.style.display = 'none';
    }, 1000);
  }
});

const game = new Phaser.Game(config);

export default game;
