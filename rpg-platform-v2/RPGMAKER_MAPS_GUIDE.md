# 使用 RPG Maker 現有地圖

## 📋 概述

本工具可以將 `AI-Agentv4\RPG_platform\RPG_Project\data` 中的 RPG Maker MV 地圖轉換為 Phaser 3 可用的格式。

---

## 🗺️ 可用地圖

根據 `MapInfos.json`，以下地圖可供使用：

### 主要區域
1. **Map002 - Forest Town** (森林小鎮)
   - 尺寸: 40x40 tiles
   - Tileset ID: 2
   - 主城鎮地圖

2. **Map014 - Shop District** (商店區)
   - 尺寸: 31x29 tiles
   - Tileset ID: 5
   - 商業區域

### 建築物
3. **Map003 - Weapon Shop** (武器店)
4. **Map004 - Start house** (起始房屋)
5. **Map006 - Armor Shop** (防具店)
6. **Map007 - Inn 1F** (旅館1樓)
7. **Map008 - Inn 2F** (旅館2樓)
8. **Map012 - Item Shop** (道具店)
9. **Map013 - Restaurant** (餐廳)

### 住宅
10. **Map005 - House 1**
11. **Map009 - NPC House 1**
12. **Map010 - NPC House 2**
13. **Map011 - NPC House 3**
14. **Map015 - Item Shop** (商店區道具店)
15. **Map016 - NPC House 1** (商店區住宅1)
16. **Map017 - NPC House 2** (商店區住宅2)

### 特殊區域
17. **Map001 - Park** (公園)
18. **Map018 - Casino** (賭場)

---

## 🚀 使用步驟

### 1. 運行地圖轉換器

```bash
cd C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2
node tools/rpgmaker-map-converter.js
```

這將會：
- ✅ 讀取所有 RPG Maker 地圖文件
- ✅ 轉換為 Phaser Tilemap JSON 格式
- ✅ 保存到 `public/assets/maps/` 目錄
- ✅ 生成地圖索引文件 `map-index.json`

### 2. 轉換結果

轉換後的文件結構：
```
public/assets/maps/
├── Forest_Town.json          (Map002)
├── Shop_District.json        (Map014)
├── Weapon_Shop.json          (Map003)
├── Start_house.json          (Map004)
├── ...
└── map-index.json            (地圖索引)
```

---

## 📊 地圖數據結構

### RPG Maker MV 格式
```json
{
  "width": 40,
  "height": 40,
  "tilesetId": 2,
  "data": [2816, 2816, ...],  // 4層數據 (Ground, Lower, Upper, Shadow)
  "events": [...]              // NPC 和事件
}
```

### Phaser 3 格式
```json
{
  "width": 40,
  "height": 40,
  "tilewidth": 48,
  "tileheight": 48,
  "layers": [
    { "name": "Ground", "data": [...] },
    { "name": "Lower", "data": [...] },
    { "name": "Upper", "data": [...] },
    { "name": "Shadow", "data": [...] },
    { "name": "Events", "objects": [...] }
  ]
}
```

---

## 🎮 在遊戲中使用

### 方法 1: 直接加載轉換後的地圖

```typescript
// src/scenes/WorldMapScene.ts
create(): void {
  // 加載 Forest Town 地圖
  this.map = this.make.tilemap({ key: 'forest-town' });
  
  // 添加 tileset
  const tileset = this.map.addTilesetImage('Outside_A2', 'tileset-outside');
  
  // 創建圖層
  const groundLayer = this.map.createLayer('Ground', tileset);
  const lowerLayer = this.map.createLayer('Lower', tileset);
  const upperLayer = this.map.createLayer('Upper', tileset);
  
  // 設置深度
  groundLayer.setDepth(0);
  lowerLayer.setDepth(1);
  upperLayer.setDepth(100);
}
```

### 方法 2: 使用地圖索引動態加載

```typescript
// src/scenes/BootScene.ts
preload(): void {
  // 加載地圖索引
  this.load.json('map-index', 'assets/maps/map-index.json');
  
  // 加載所有地圖
  const mapIndex = this.cache.json.get('map-index');
  mapIndex.maps.forEach(map => {
    this.load.tilemapTiledJSON(map.id, `assets/maps/${map.file}`);
  });
}
```

---

## 🔧 高級功能

### 1. 提取 NPC 位置

```typescript
// 從地圖事件層獲取 NPC 位置
const eventLayer = this.map.getObjectLayer('Events');
eventLayer.objects.forEach(obj => {
  if (obj.type === 'event') {
    const npc = new NPC(this, obj.x, obj.y, 'elderly');
    this.npcs.push(npc);
  }
});
```

### 2. 設置碰撞

```typescript
// 設置特定 tile 為碰撞
groundLayer.setCollisionByProperty({ collides: true });

// 與玩家設置碰撞
this.physics.add.collider(this.player.sprite, groundLayer);
```

### 3. 地圖切換

```typescript
// 切換到不同地圖
switchMap(mapKey: string): void {
  // 銷毀當前地圖
  this.map.destroy();
  
  // 加載新地圖
  this.map = this.make.tilemap({ key: mapKey });
  this.createLayers();
}
```

---

## 📝 注意事項

### Tileset 對應關係

RPG Maker MV 使用的 Tileset ID 需要對應到正確的圖片：

| Tileset ID | RPG Maker 文件 | Phaser 資源 |
|------------|---------------|-------------|
| 1 | Inside_A | tileset-inside |
| 2 | Outside_A | tileset-outside |
| 5 | SF_Outside_A | tileset-sf-outside |

### 圖層深度設置

```typescript
Ground Layer:  depth = 0   (地面)
Lower Layer:   depth = 1   (裝飾、道路)
Player/NPC:    depth = 10  (角色)
Upper Layer:   depth = 100 (建築頂部、橋樑)
Shadow Layer:  depth = 0.5 (陰影)
```

### Tile ID 轉換

RPG Maker 的 tile ID 可能需要調整：
- RPG Maker: 從 0 開始
- Phaser: 從 1 開始 (0 = 空白)

轉換器已自動處理此問題。

---

## 🐛 故障排除

### 問題 1: 地圖顯示空白
**原因**: Tileset 圖片未正確加載
**解決**: 確保 tileset 圖片在 `public/assets/tilesets/` 目錄

### 問題 2: Tile 顯示錯誤
**原因**: Tileset ID 對應錯誤
**解決**: 檢查 `tilesetId` 並使用正確的 tileset 圖片

### 問題 3: NPC 位置不正確
**原因**: 坐標系統差異
**解決**: RPG Maker 使用 tile 坐標，需要乘以 48 轉換為像素

---

## 📊 轉換統計

運行轉換器後會顯示：

```
============================================================
RPG Maker MV 地圖轉換器
============================================================

轉換地圖: Forest Town
尺寸: 40x40
Tileset ID: 2
✅ 已保存: public/assets/maps/Forest_Town.json

轉換地圖: Shop District
尺寸: 31x29
Tileset ID: 5
✅ 已保存: public/assets/maps/Shop_District.json

...

============================================================
轉換完成統計
============================================================
總地圖數: 18
成功: 18
失敗: 0

📋 地圖索引已生成: public/assets/maps/map-index.json

✨ 所有地圖轉換完成！
```

---

## 🎯 下一步

1. ✅ 運行轉換器
2. ✅ 檢查生成的地圖文件
3. ✅ 更新 BootScene 加載地圖
4. ✅ 更新 WorldMapScene 使用新地圖
5. ✅ 測試地圖顯示和碰撞

---

## 📚 相關文檔

- [RPG Maker MV 文檔](https://www.rpgmakerweb.com/support/products/rpg-maker-mv)
- [Phaser 3 Tilemap 教程](https://phaser.io/tutorials/making-your-first-phaser-3-game/part9)
- [Tiled Map Editor](https://www.mapeditor.org/)

---

*最後更新: 2026-02-04*
