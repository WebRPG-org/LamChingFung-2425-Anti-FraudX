/**
 * RPG Maker MV Map Converter
 * 將 RPG Maker MV 的地圖數據轉換為 Phaser 3 Tilemap JSON 格式
 */

const fs = require('fs');
const path = require('path');

class RPGMakerMapConverter {
  constructor(rpgMakerDataPath, outputPath) {
    this.rpgMakerDataPath = rpgMakerDataPath;
    this.outputPath = outputPath;
    this.tilesetsData = null;
    this.loadTilesets();
  }

  /**
   * 讀取 Tilesets 數據（包含碰撞標記）
   */
  loadTilesets() {
    try {
      const tilesetsFile = path.join(this.rpgMakerDataPath, 'Tilesets.json');
      const tilesetsContent = fs.readFileSync(tilesetsFile, 'utf8');
      this.tilesetsData = JSON.parse(tilesetsContent);
      console.log(`✓ 已載入 ${this.tilesetsData.length} 個 Tileset（含碰撞數據）\n`);
    } catch (error) {
      console.warn('⚠ 無法載入 Tilesets.json，碰撞數據將不可用\n');
    }
  }

  /**
   * 獲取 Tileset 的碰撞標記
   */
  getTilesetFlags(tilesetId) {
    if (!this.tilesetsData || !this.tilesetsData[tilesetId]) {
      return null;
    }
    return this.tilesetsData[tilesetId].flags;
  }

  /**
   * 讀取 RPG Maker 地圖文件
   */
  loadRPGMakerMap(mapId) {
    const mapFile = path.join(this.rpgMakerDataPath, `Map${String(mapId).padStart(3, '0')}.json`);
    const mapData = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
    return mapData;
  }

  /**
   * 讀取地圖資訊
   */
  loadMapInfos() {
    const mapInfosFile = path.join(this.rpgMakerDataPath, 'MapInfos.json');
    const mapInfos = JSON.parse(fs.readFileSync(mapInfosFile, 'utf8'));
    return mapInfos;
  }

  /**
   * 轉換 RPG Maker 地圖數據為 Phaser Tilemap JSON
   */
  convertMap(mapId) {
    const rpgMap = this.loadRPGMakerMap(mapId);
    const mapInfos = this.loadMapInfos();
    const mapInfo = mapInfos[mapId];

    console.log(`\n轉換地圖: ${mapInfo ? mapInfo.name : `Map ${mapId}`}`);
    console.log(`尺寸: ${rpgMap.width}x${rpgMap.height}`);
    console.log(`Tileset ID: ${rpgMap.tilesetId}`);

    // RPG Maker MV 的地圖數據結構:
    // data 陣列包含多層數據，每層大小為 width * height
    // 層級順序: Ground, Lower, Upper, Shadow (4層)
    const layerCount = 4;
    const tileCount = rpgMap.width * rpgMap.height;

    // 提取各層數據
    const layers = [];
    for (let i = 0; i < layerCount; i++) {
      const layerData = rpgMap.data.slice(i * tileCount, (i + 1) * tileCount);
      layers.push(layerData);
    }

    // 獲取 Tileset 碰撞標記（空氣牆數據）
    const tilesetFlags = this.getTilesetFlags(rpgMap.tilesetId);

    // 創建 Phaser Tilemap JSON 格式（使用嵌入式 tileset）
    const phaserMap = {
      compressionlevel: -1,
      height: rpgMap.height,
      width: rpgMap.width,
      infinite: false,
      layers: [
        this.createLayer('Ground', layers[0], rpgMap.width, rpgMap.height, 0),
        this.createLayer('Lower', layers[1], rpgMap.width, rpgMap.height, 1),
        this.createLayer('Upper', layers[2], rpgMap.width, rpgMap.height, 2),
        this.createLayer('Shadow', layers[3], rpgMap.width, rpgMap.height, 3)
      ],
      nextlayerid: 5,
      nextobjectid: 1,
      orientation: 'orthogonal',
      renderorder: 'right-down',
      tiledversion: '1.10.2',
      tileheight: 48,
      tilewidth: 48,
      tilesets: [
        {
          columns: 16,
          firstgid: 1,
          image: 'tileset-outside.png',
          imageheight: 768,
          imagewidth: 768,
          margin: 0,
          name: 'tileset-outside',
          spacing: 0,
          tilecount: 256,
          tileheight: 48,
          tilewidth: 48
        }
      ],
      type: 'map',
      version: '1.10'
    };

    // 碰撞標記數據太大，暫時不包含在地圖文件中
    // 將使用手動配置的碰撞規則
    console.log(`✓ 地圖轉換完成（碰撞數據將使用手動配置）`);

    // 添加事件對象層
    if (rpgMap.events && rpgMap.events.length > 0) {
      const objectLayer = this.createObjectLayer(rpgMap.events, rpgMap.width, rpgMap.height);
      phaserMap.layers.push(objectLayer);
    }

    return phaserMap;
  }

  /**
   * 映射 RPG Maker 瓦片 ID 到 Phaser 範圍 (1-256)
   * RPG Maker MV 使用多個 tileset 的組合 ID
   * 
   * 重要：保持 autotile 的相對位置關係
   */
  mapTileId(rpgMakerTileId) {
    if (rpgMakerTileId === 0) return 0; // 空瓦片
    
    // RPG Maker MV tileset 結構:
    // 2048-2815: Tileset A2 (ground autotiles) - 768 tiles
    // 我們的 Outside_A2.png 是 256 tiles (16x16)
    
    // 對於 A2 tileset (2048-2815)，直接映射到我們的 tileset
    if (rpgMakerTileId >= 2048 && rpgMakerTileId < 2816) {
      // A2 autotiles: 每個 autotile 佔用 48 個 tile ID
      // 計算是第幾個 autotile 和內部偏移
      const a2Offset = rpgMakerTileId - 2048;
      const autotileIndex = Math.floor(a2Offset / 48);
      const tileOffset = a2Offset % 48;
      
      // 映射到我們的 256 tile tileset
      // 每個 autotile 在我們的 tileset 中佔用 3x4 = 12 tiles
      // 但 RPG Maker 使用 48 個 ID，所以我們需要壓縮
      const mappedAutotile = autotileIndex % 16; // 最多 16 個 autotiles
      const mappedOffset = Math.floor(tileOffset / 4); // 壓縮 48 -> 12
      
      const result = mappedAutotile * 16 + mappedOffset + 1;
      return Math.min(result, 256);
    }
    
    // 對於其他 tileset，使用簡單映射
    if (rpgMakerTileId >= 2816) {
      return ((rpgMakerTileId - 2816) % 256) + 1;
    }
    
    if (rpgMakerTileId >= 1536) {
      return ((rpgMakerTileId - 1536) % 256) + 1;
    }
    
    return (rpgMakerTileId % 256) + 1;
  }

  /**
   * 創建圖層
   */
  createLayer(name, data, width, height, id) {
    // 映射所有瓦片 ID 到 Phaser 範圍
    const mappedData = data.map(tileId => this.mapTileId(tileId));
    
    return {
      data: mappedData,
      height: height,
      width: width,
      id: id + 1,
      name: name,
      opacity: 1,
      type: 'tilelayer',
      visible: true,
      x: 0,
      y: 0
    };
  }

  /**
   * 創建對象層 (NPC, 事件等)
   */
  createObjectLayer(events, mapWidth, mapHeight) {
    const objects = [];
    
    events.forEach((event, index) => {
      if (!event) return;
      
      objects.push({
        id: index + 1,
        name: event.name,
        type: 'event',
        x: event.x * 48,
        y: event.y * 48,
        width: 48,
        height: 48,
        rotation: 0,
        visible: true,
        properties: [
          { name: 'eventId', type: 'int', value: event.id },
          { name: 'note', type: 'string', value: event.note || '' }
        ]
      });
    });

    return {
      id: 5,
      name: 'Events',
      objects: objects,
      opacity: 1,
      type: 'objectgroup',
      visible: true,
      x: 0,
      y: 0
    };
  }

  /**
   * 保存轉換後的地圖
   */
  saveMap(mapId, phaserMap) {
    const mapInfos = this.loadMapInfos();
    const mapInfo = mapInfos[mapId];
    const mapName = mapInfo ? mapInfo.name.replace(/[^a-zA-Z0-9]/g, '_') : `map_${mapId}`;
    
    const outputFile = path.join(this.outputPath, `${mapName}.json`);
    fs.writeFileSync(outputFile, JSON.stringify(phaserMap, null, 2), 'utf8');
    
    console.log(`✅ 已保存: ${outputFile}`);
    return outputFile;
  }

  /**
   * 轉換所有地圖
   */
  convertAllMaps() {
    const mapInfos = this.loadMapInfos();
    const results = [];

    console.log('='.repeat(60));
    console.log('RPG Maker MV 地圖轉換器');
    console.log('='.repeat(60));

    mapInfos.forEach((mapInfo, index) => {
      if (!mapInfo || index === 0) return; // 跳過 null 和索引 0
      
      try {
        const phaserMap = this.convertMap(index);
        const outputFile = this.saveMap(index, phaserMap);
        results.push({
          id: index,
          name: mapInfo.name,
          file: outputFile,
          success: true
        });
      } catch (error) {
        console.error(`❌ 轉換失敗 Map${String(index).padStart(3, '0')}: ${error.message}`);
        results.push({
          id: index,
          name: mapInfo.name,
          success: false,
          error: error.message
        });
      }
    });

    console.log('\n' + '='.repeat(60));
    console.log('轉換完成統計');
    console.log('='.repeat(60));
    console.log(`總地圖數: ${results.length}`);
    console.log(`成功: ${results.filter(r => r.success).length}`);
    console.log(`失敗: ${results.filter(r => !r.success).length}`);
    
    return results;
  }

  /**
   * 生成地圖索引文件
   */
  generateMapIndex(results) {
    const index = {
      maps: results.filter(r => r.success).map(r => ({
        id: r.id,
        name: r.name,
        file: path.basename(r.file)
      }))
    };

    const indexFile = path.join(this.outputPath, 'map-index.json');
    fs.writeFileSync(indexFile, JSON.stringify(index, null, 2), 'utf8');
    console.log(`\n📋 地圖索引已生成: ${indexFile}`);
  }
}

// 主程序
if (require.main === module) {
  const rpgMakerDataPath = path.join(__dirname, '../../RPG_platform/RPG_Project/data');
  const outputPath = path.join(__dirname, '../public/assets/maps');

  // 確保輸出目錄存在
  if (!fs.existsSync(outputPath)) {
    fs.mkdirSync(outputPath, { recursive: true });
  }

  const converter = new RPGMakerMapConverter(rpgMakerDataPath, outputPath);
  
  // 轉換所有地圖
  const results = converter.convertAllMaps();
  
  // 生成索引
  converter.generateMapIndex(results);

  console.log('\n✨ 所有地圖轉換完成！');
}

module.exports = RPGMakerMapConverter;
