# 🎨 使用 RPG Maker MV 專業素材指南

## ✅ 已完成

成功從 `RPG_platform\RPG_Project` 複製了 **381 個專業素材**！

### 📊 素材統計

| 類別 | 數量 | 說明 |
|------|------|------|
| **角色精靈圖** | 29 個 | Actor1-3, People1-4, Monster, Evil 等 |
| **瓦片集** | 31 個 | Inside/Outside/Dungeon 完整瓦片 |
| **戰鬥背景** | 77 個 | 50 個地面 + 27 個天空背景 |
| **敵人圖片** | 70 個 | Bat, Slime, Dragon, Demon 等 |
| **動畫效果** | 117 個 | Fire, Ice, Thunder, Slash 等 |
| **系統 UI** | 14 個 | Window, IconSet, Balloon 等 |
| **地圖背景** | 20 個 | 標題畫面和大型背景 |

**總計**: 381 個檔案，196.93 MB

---

## 📂 素材結構

```
rpg-platform-v2/public/assets/
├── characters/          ← 29 個角色精靈圖
│   ├── Actor1.png      (主角 1)
│   ├── Actor2.png      (主角 2)
│   ├── Actor3.png      (主角 3)
│   ├── People1.png     (NPC 1)
│   ├── People2.png     (NPC 2)
│   ├── People3.png     (NPC 3)
│   ├── People4.png     (NPC 4)
│   ├── Monster.png     (怪物)
│   ├── Evil.png        (邪惡角色)
│   ├── !Chest.png      (寶箱)
│   ├── !Door1.png      (門 1)
│   └── Vehicle.png     (交通工具)
│
├── tilesets/           ← 31 個瓦片集
│   ├── Inside_A1.png   (室內自動瓦片)
│   ├── Inside_A2.png   (室內地面)
│   ├── Inside_B.png    (室內牆壁)
│   ├── Inside_C.png    (室內裝飾)
│   ├── Outside_A1.png  (室外自動瓦片)
│   ├── Outside_A2.png  (室外地面)
│   ├── Outside_B.png   (室外建築)
│   ├── Outside_C.png   (室外裝飾)
│   └── Dungeon_*.png   (地下城瓦片)
│
├── battlebacks/        ← 77 個戰鬥背景
│   ├── Ruins2.png      (廢墟地面)
│   ├── Town2.png       (城鎮天空)
│   ├── Castle1.png     (城堡)
│   ├── Forest.png      (森林)
│   └── ...
│
├── enemies/            ← 70 個敵人圖片
│   ├── Bat.png         (蝙蝠)
│   ├── Slime.png       (史萊姆)
│   ├── Dragon.png      (龍)
│   ├── Demon.png       (惡魔)
│   └── ...
│
├── animations/         ← 117 個動畫效果
│   ├── Fire1.png       (火焰 1)
│   ├── Ice1.png        (冰凍 1)
│   ├── Thunder1.png    (雷電 1)
│   ├── Slash.png       (斬擊)
│   └── ...
│
├── system/             ← 14 個系統 UI
│   ├── Window.png      (視窗皮膚)
│   ├── IconSet.png     (圖示集)
│   ├── Balloon.png     (表情氣泡)
│   └── ...
│
└── maps/               ← 20 個地圖背景
    ├── Castle.png      (城堡)
    ├── Medieval.png    (中世紀)
    └── ...
```

---

## 🎮 在 Phaser 中使用

### 1. 載入角色精靈圖

```typescript
// 在 BootScene.ts 中載入
preload() {
    // 載入主角（48x48 像素，3列4行）
    this.load.spritesheet('actor1', 'assets/characters/Actor1.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    // 載入 NPC
    this.load.spritesheet('people1', 'assets/characters/People1.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    // 載入互動物件
    this.load.spritesheet('chest', 'assets/characters/!Chest.png', {
        frameWidth: 48,
        frameHeight: 48
    });
}

// 在 WorldMapScene.ts 中使用
create() {
    // 創建玩家
    this.player = this.add.sprite(400, 300, 'actor1');
    
    // 創建行走動畫
    this.anims.create({
        key: 'walk-down',
        frames: this.anims.generateFrameNumbers('actor1', { start: 0, end: 2 }),
        frameRate: 8,
        repeat: -1
    });
    
    this.anims.create({
        key: 'walk-left',
        frames: this.anims.generateFrameNumbers('actor1', { start: 3, end: 5 }),
        frameRate: 8,
        repeat: -1
    });
    
    this.anims.create({
        key: 'walk-right',
        frames: this.anims.generateFrameNumbers('actor1', { start: 6, end: 8 }),
        frameRate: 8,
        repeat: -1
    });
    
    this.anims.create({
        key: 'walk-up',
        frames: this.anims.generateFrameNumbers('actor1', { start: 9, end: 11 }),
        frameRate: 8,
        repeat: -1
    });
}
```

### 2. 載入瓦片集

```typescript
preload() {
    // 載入室外瓦片
    this.load.image('outside_tiles', 'assets/tilesets/Outside_A2.png');
    this.load.image('outside_buildings', 'assets/tilesets/Outside_B.png');
    this.load.image('outside_decorations', 'assets/tilesets/Outside_C.png');
}

create() {
    // 創建瓦片地圖
    const map = this.make.tilemap({ 
        tileWidth: 48, 
        tileHeight: 48,
        width: 20,
        height: 15
    });
    
    const tileset = map.addTilesetImage('outside_tiles');
    const layer = map.createBlankLayer('ground', tileset);
}
```

### 3. 載入戰鬥背景

```typescript
// 在 BattleScene.ts 中
preload() {
    // 載入戰鬥背景（組合使用）
    this.load.image('battle_ground', 'assets/battlebacks/Ruins2.png');
    this.load.image('battle_sky', 'assets/battlebacks/Town2.png');
    
    // 載入敵人
    this.load.image('enemy_bat', 'assets/enemies/Bat.png');
}

create() {
    // 顯示背景（1000x740）
    this.add.image(400, 300, 'battle_ground').setScale(0.8);
    
    // 顯示敵人
    const enemy = this.add.image(600, 300, 'enemy_bat');
}
```

### 4. 載入動畫效果

```typescript
preload() {
    // 載入攻擊動畫（192x192 精靈表）
    this.load.spritesheet('slash_anim', 'assets/animations/Slash.png', {
        frameWidth: 192,
        frameHeight: 192
    });
    
    this.load.spritesheet('fire_anim', 'assets/animations/Fire1.png', {
        frameWidth: 192,
        frameHeight: 192
    });
}

create() {
    // 創建斬擊動畫
    this.anims.create({
        key: 'slash',
        frames: this.anims.generateFrameNumbers('slash_anim', { start: 0, end: 14 }),
        frameRate: 20,
        repeat: 0
    });
    
    // 播放動畫
    const slashEffect = this.add.sprite(400, 300, 'slash_anim');
    slashEffect.play('slash');
    slashEffect.on('animationcomplete', () => {
        slashEffect.destroy();
    });
}
```

### 5. 載入系統 UI

```typescript
preload() {
    // 載入 UI 元素
    this.load.image('window', 'assets/system/Window.png');
    this.load.image('icons', 'assets/system/IconSet.png');
    this.load.spritesheet('balloon', 'assets/system/Balloon.png', {
        frameWidth: 48,
        frameHeight: 48
    });
}
```

---

## 📐 素材規格

### 角色精靈圖
- **尺寸**: 48x48 像素/幀
- **格式**: 3列4行（12幀）
- **佈局**:
  ```
  [0][1][2]  ← 向下行走
  [3][4][5]  ← 向左行走
  [6][7][8]  ← 向右行走
  [9][10][11] ← 向上行走
  ```

### 瓦片集
- **瓦片大小**: 48x48 像素
- **A1-A4**: 自動瓦片（水、瀑布等）
- **A5**: 普通瓦片
- **B**: 牆壁和建築
- **C**: 裝飾物

### 戰鬥背景
- **尺寸**: 1000x740 像素
- **使用**: battlebacks1（地面）+ battlebacks2（天空）

### 動畫
- **尺寸**: 192x192 像素/幀
- **幀數**: 通常 15-30 幀
- **格式**: 5列 x N行

---

## 🎨 推薦組合

### 香港街道場景
```typescript
// 瓦片
'Outside_A2.png'  // 道路和地面
'Outside_B.png'   // 建築物
'Outside_C.png'   // 裝飾（樹木、路燈）

// 角色
'People1.png'     // 市民
'People2.png'     // 商人
'Actor1.png'      // 玩家
```

### 反詐騙訓練場景
```typescript
// 戰鬥背景
'Town2.png'       // 城市背景

// 角色
'People3.png'     // 受害者（長者）
'Evil.png'        // 詐騙犯

// 動畫
'Phone.png'       // 電話效果
'Confusion.png'   // 困惑狀態
```

### 室內辦公室場景
```typescript
// 瓦片
'Inside_A1.png'   // 地板
'Inside_B.png'    // 牆壁和家具
'Inside_C.png'    // 裝飾

// 物件
'!Door1.png'      // 門
'!Chest.png'      // 文件櫃
```

---

## 🔧 更新現有代碼

### 更新 BootScene.ts

```typescript
preload() {
    // 載入專業角色素材
    this.load.spritesheet('player', 'assets/characters/Actor1.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    this.load.spritesheet('npc-scammer', 'assets/characters/Evil.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    this.load.spritesheet('npc-expert', 'assets/characters/People1.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    this.load.spritesheet('npc-victim', 'assets/characters/People3.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    
    // 載入地圖瓦片
    this.load.image('tileset', 'assets/tilesets/Outside_A2.png');
    
    // 載入戰鬥背景
    this.load.image('battle-bg', 'assets/battlebacks/Town2.png');
}
```

### 更新 WorldMapScene.ts

```typescript
create() {
    // 使用專業瓦片集創建地圖
    const map = this.make.tilemap({
        tileWidth: 48,
        tileHeight: 48,
        width: 30,
        height: 20
    });
    
    const tileset = map.addTilesetImage('tileset');
    const groundLayer = map.createBlankLayer('ground', tileset);
    
    // 填充草地
    for (let y = 0; y < 20; y++) {
        for (let x = 0; x < 30; x++) {
            groundLayer.putTileAt(0, x, y);
        }
    }
}
```

---

## 📚 資源參考

### RPG Maker MV 規格
- **官方文檔**: https://www.rpgmakerweb.com/
- **瓦片標準**: 48x48 像素
- **角色標準**: 48x48 像素，12幀動畫
- **動畫標準**: 192x192 像素

### Phaser 3 文檔
- **精靈表**: https://photonstorm.github.io/phaser3-docs/Phaser.Loader.LoaderPlugin.html#spritesheet
- **瓦片地圖**: https://photonstorm.github.io/phaser3-docs/Phaser.Tilemaps.Tilemap.html
- **動畫**: https://photonstorm.github.io/phaser3-docs/Phaser.Animations.AnimationManager.html

---

## 🎉 總結

您現在擁有：

✅ **381 個專業 RPG Maker MV 素材**  
✅ **196.93 MB 高品質圖片**  
✅ **完整的角色、地圖、戰鬥系統素材**  
✅ **即用即玩的專業級資源**  

### 下一步

1. ✅ **素材已複製** - 檢查 `public/assets/` 資料夾
2. 🔄 **更新代碼** - 使用上面的範例更新場景
3. 🎮 **測試遊戲** - 運行 `npm run dev` 查看效果
4. 🎨 **自訂場景** - 根據需求選擇合適的素材組合

---

**準備好使用專業素材開發遊戲了嗎？** 🚀

所有素材都已就緒，開始創建您的反詐騙 RPG 遊戲吧！
