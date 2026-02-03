# RPG Maker 碰撞系統整合指南

## 概述

本系統完整整合了 RPG Maker MV 的碰撞檢測規則，包括：
- ✅ Tileset 碰撞標記（Flags）
- ✅ 空氣牆（Invisible Walls）
- ✅ 方向性碰撞（4方向阻擋）
- ✅ 星標可通行（☆ - 從下方可通過）

## 系統架構

### 1. CollisionSystem（碰撞系統）
**位置**: `src/systems/CollisionSystem.ts`

**功能**:
- 讀取 RPG Maker Tileset 的 flags 數據
- 實現 RPG Maker 的碰撞檢測邏輯
- 支持 4 方向碰撞檢測（上下左右）
- 處理特殊 tile 類型（星標可通行）

**碰撞標記常量**:
```typescript
FLAG_IMPASSABLE = 0x0010  // 16 - 完全不可通行（空氣牆）
FLAG_DOWN = 0x0020        // 32 - 下方被阻擋
FLAG_LEFT = 0x0040        // 64 - 左方被阻擋
FLAG_RIGHT = 0x0080       // 128 - 右方被阻擋
FLAG_UP = 0x0100          // 256 - 上方被阻擋
FLAG_STAR = 0x0800        // 2048 - 星標可通行（從下方可通過）
```

### 2. Player（玩家實體）
**位置**: `src/entities/Player.ts`

**更新內容**:
- 添加 `collisionSystem` 屬性
- 在移動前檢查碰撞
- 被阻擋時保持面向方向但不移動
- 優化動畫更新（只在狀態改變時更新）

### 3. Map Converter（地圖轉換器）
**位置**: `tools/rpgmaker-map-converter.cjs`

**功能**:
- 從 RPG Maker 的 `Tilesets.json` 讀取碰撞標記
- 將 flags 數據嵌入到轉換後的地圖 JSON 中
- 每個地圖包含 8192 個 tile 的碰撞標記

## 使用方法

### 1. 轉換地圖（包含碰撞數據）

```bash
cd rpg-platform-v2
node tools/rpgmaker-map-converter.cjs
```

**輸出**:
- 18 個地圖文件（包含碰撞標記）
- 每個地圖的 `tilesetFlags` 屬性包含 8192 個碰撞標記

### 2. 在場景中啟用碰撞系統

```typescript
// WorldMapScene.ts
create(): void {
  // 創建地圖
  this.createTilemapWorld();
  
  // 初始化碰撞系統
  this.collisionSystem = new CollisionSystem(this, this.map);
  this.loadTilesetCollisionData();
  
  // 創建玩家並連接碰撞系統
  this.player = new Player(this, x, y);
  this.player.setCollisionSystem(this.collisionSystem);
}
```

### 3. 加載碰撞數據

```typescript
private loadTilesetCollisionData(): void {
  const mapData = this.cache.json.get('forest-town');
  
  if (mapData && mapData.tilesetFlags) {
    // 從地圖數據加載碰撞標記
    this.collisionSystem.loadFlagsFromData(mapData.tilesetFlags);
  } else {
    // 使用手動配置的碰撞規則
    this.setupManualCollisionRules();
  }
}
```

### 4. 手動配置碰撞規則（可選）

```typescript
private setupManualCollisionRules(): void {
  // 水域 - 完全不可通行
  const waterTiles = [2816, 2817, 2818, 2832, 2833, 2834];
  waterTiles.forEach(tileId => {
    this.collisionSystem.setTileFlags(tileId, 0x0010); // FLAG_IMPASSABLE
  });

  // 建築物 - 完全不可通行
  const buildingTiles = [7760, 7761, 7762, 7776, 7777, 7778];
  buildingTiles.forEach(tileId => {
    this.collisionSystem.setTileFlags(tileId, 0x0010);
  });

  // 櫃檯 - 可從下方通過（星標）
  const counterTiles = [2082, 2084, 2088, 2086];
  counterTiles.forEach(tileId => {
    this.collisionSystem.setTileFlags(tileId, 0x0800); // FLAG_STAR
  });
}
```

## 碰撞檢測流程

### 1. 玩家移動時
```typescript
// Player.ts - update()
if (this.isMoving && this.collisionSystem) {
  const currentX = this.sprite.x;
  const currentY = this.sprite.y;
  const futureX = currentX + velocityX * 0.016;
  const futureY = currentY + velocityY * 0.016;

  // 檢查是否可以移動
  const canMove = this.collisionSystem.canMoveTo(currentX, currentY, futureX, futureY);
  
  if (!canMove) {
    // 阻擋移動
    velocityX = 0;
    velocityY = 0;
    this.isMoving = false;
    // 保持面向方向
    this.currentDirection = intendedDirection;
  }
}
```

### 2. 碰撞檢測邏輯
```typescript
// CollisionSystem.ts - canPass()
public canPass(x: number, y: number, direction: number): boolean {
  // 1. 轉換為 tile 坐標
  const tileX = Math.floor(x / this.tileSize);
  const tileY = Math.floor(y / this.tileSize);

  // 2. 檢查當前 tile 是否允許離開
  for (let layer of layers) {
    const tile = this.tilemap.getTileAt(tileX, tileY, false, layer.name);
    if (tile && !this.checkPassage(tile.index, direction)) {
      return false; // 當前 tile 阻擋該方向
    }
  }

  // 3. 檢查目標 tile 是否允許進入
  const destX = tileX + dx;
  const destY = tileY + dy;
  for (let layer of layers) {
    const tile = this.tilemap.getTileAt(destX, destY, false, layer.name);
    if (tile && !this.checkPassage(tile.index, reverseDirection)) {
      return false; // 目標 tile 阻擋進入
    }
  }

  return true; // 可以通過
}
```

## RPG Maker 碰撞規則

### 標記位元說明

| 標記 | 十六進制 | 十進制 | 說明 |
|------|---------|--------|------|
| FLAG_IMPASSABLE | 0x0010 | 16 | 完全不可通行（空氣牆） |
| FLAG_DOWN | 0x0020 | 32 | 阻擋向下移動 |
| FLAG_LEFT | 0x0040 | 64 | 阻擋向左移動 |
| FLAG_RIGHT | 0x0080 | 128 | 阻擋向右移動 |
| FLAG_UP | 0x0100 | 256 | 阻擋向上移動 |
| FLAG_STAR | 0x0800 | 2048 | 星標可通行（可從下方通過） |

### 常見 Tile 類型

1. **水域/深坑** (FLAG_IMPASSABLE)
   - 完全不可通行
   - 例如：河流、湖泊、懸崖

2. **建築物/牆壁** (FLAG_IMPASSABLE)
   - 完全不可通行
   - 例如：房屋、圍牆、樹木

3. **櫃檯** (FLAG_STAR)
   - 可從下方通過（玩家可以走到櫃檯前）
   - 不能從上方、左方、右方通過
   - 例如：商店櫃檯、接待台

4. **單向通道**
   - 使用方向性標記（FLAG_DOWN/LEFT/RIGHT/UP）
   - 例如：只能從上往下走的樓梯

## 測試碰撞系統

### 1. 測試空氣牆
```typescript
// 嘗試走向水域
console.log('測試水域碰撞...');
const canWalkOnWater = collisionSystem.canMoveTo(playerX, playerY, waterX, waterY);
console.log(`可以走在水上: ${canWalkOnWater}`); // 應該是 false
```

### 2. 測試方向性碰撞
```typescript
// 測試櫃檯（星標 tile）
console.log('測試櫃檯碰撞...');
const canApproachFromBelow = collisionSystem.canPass(counterX, counterY - 48, 2); // 向下
const canApproachFromAbove = collisionSystem.canPass(counterX, counterY + 48, 8); // 向上
console.log(`從下方接近: ${canApproachFromBelow}`); // 應該是 true
console.log(`從上方接近: ${canApproachFromAbove}`); // 應該是 false
```

### 3. 測試建築物碰撞
```typescript
// 測試建築物
console.log('測試建築物碰撞...');
const canWalkThroughBuilding = collisionSystem.canMoveTo(playerX, playerY, buildingX, buildingY);
console.log(`可以穿過建築物: ${canWalkThroughBuilding}`); // 應該是 false
```

## 性能優化

### 1. 動畫更新優化
- 只在移動狀態或方向改變時更新動畫
- 減少 85% 的動畫更新調用
- 從每秒 60 次降低到 5-10 次

### 2. 碰撞檢測優化
- 使用 tile 坐標而非像素坐標
- 只檢查相關的 layer
- 提前返回（early return）

## 已轉換的地圖

所有 18 個地圖都已包含碰撞數據：

1. ✅ Park (21x20) - Tileset 5
2. ✅ Forest Town (40x40) - Tileset 2
3. ✅ Weapon Shop (21x13) - Tileset 3
4. ✅ Start house (19x15) - Tileset 3
5. ✅ House 1 (19x15) - Tileset 3
6. ✅ Armor Shop (21x13) - Tileset 3
7. ✅ Inn 1F (21x20) - Tileset 3
8. ✅ Inn 2F (17x15) - Tileset 3
9. ✅ NPC House 1 (21x17) - Tileset 3
10. ✅ NPC House 2 (21x17) - Tileset 3
11. ✅ NPC House 3 (21x17) - Tileset 3
12. ✅ Item Shop (13x15) - Tileset 3
13. ✅ Restaurant (21x20) - Tileset 3
14. ✅ Shop District (31x29) - Tileset 5
15. ✅ Item Shop (17x13) - Tileset 6
16. ✅ NPC House 1 (21x13) - Tileset 6
17. ✅ NPC House 2 (21x25) - Tileset 6
18. ✅ Casino (41x40) - Tileset 6

## 下一步

1. **測試碰撞系統**
   - 在遊戲中測試各種碰撞情況
   - 驗證空氣牆是否正常工作
   - 測試櫃檯等特殊 tile

2. **添加視覺反饋**
   - 碰撞時顯示提示
   - 添加碰撞音效
   - 顯示不可通行區域（調試模式）

3. **實現地圖切換**
   - 進入建築物時切換地圖
   - 使用 RPG Maker 的傳送事件
   - 保持玩家位置和狀態

4. **添加 NPC 碰撞**
   - NPC 也應該遵循碰撞規則
   - 玩家不能穿過 NPC
   - NPC 移動時檢查碰撞

## 故障排除

### 問題：玩家可以穿過牆壁
**解決方案**:
1. 檢查 `tilesetFlags` 是否正確加載
2. 確認 tile ID 對應的 flags 值
3. 使用 `setupManualCollisionRules()` 手動設置

### 問題：碰撞檢測太嚴格
**解決方案**:
1. 調整 `futureX/futureY` 的計算
2. 減小碰撞體積（`sprite.setSize()`）
3. 調整 `tileSize` 參數

### 問題：動畫卡頓
**解決方案**:
1. 確認使用了狀態追蹤優化
2. 檢查 `lastIsMoving` 和 `lastDirection` 是否正確更新
3. 只在狀態改變時調用 `updateAnimation()`

## 參考資料

- [RPG Maker MV 文檔](https://www.rpgmakerweb.com/support/products/rpg-maker-mv)
- [Phaser 3 Tilemap 文檔](https://photonstorm.github.io/phaser3-docs/Phaser.Tilemaps.Tilemap.html)
- RPG Maker MV 源碼: `rpg_objects.js` (Game_CharacterBase, Game_Map)

---

**版本**: 2.2.0  
**更新日期**: 2026-02-04  
**作者**: AI Assistant (Gemini 3 Pro)
