// 專業級 RPG 地圖生成器
// 大型精緻地圖系統

let currentMap = null;
let currentTileset = null;

// ============================================================================
// 配置和常量
// ============================================================================

const CONFIG = {
    tileSize: 32,
    colors: {
        grass: ['#7cb342', '#8bc34a', '#9ccc65', '#aed581'],
        grassDark: ['#689f38', '#7cb342', '#8bc34a', '#9ccc65'],
        road: '#8d6e63',
        roadDark: '#6d4c41',
        roadLine: '#5d4037',
        building: '#e0e0e0',
        buildingDark: '#bdbdbd',
        roofRed: '#d32f2f',
        roofBlue: '#1976d2',
        roofOrange: '#f57c00',
        roofGreen: '#388e3c',
        roofPurple: '#7b1fa2',
        window: '#64b5f6',
        windowDark: '#1976d2',
        door: '#8d6e63',
        doorDark: '#5d4037',
        tree: '#2e7d32',
        treeDark: '#1b5e20',
        treeLight: '#43a047',
        trunk: '#8d6e63',
        flower: ['#f44336', '#e91e63', '#9c27b0', '#ffeb3b'],
        stone: '#78909c',
        stoneDark: '#546e7a',
        water: '#1976d2',
        waterLight: '#42a5f5',
        sidewalk: '#9e9e9e',
        sidewalkDark: '#757575'
    }
};

// ============================================================================
// 工具函數
// ============================================================================

function createCanvas(width, height) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    return canvas;
}

function getRandomColor(colors) {
    return Array.isArray(colors) ? colors[Math.floor(Math.random() * colors.length)] : colors;
}

// ============================================================================
// 地形繪製函數
// ============================================================================

function drawGrassTile(ctx, x, y, variant = 0) {
    const baseColor = CONFIG.colors.grass[variant % 4];
    const darkColor = CONFIG.colors.grassDark[variant % 4];
    
    ctx.fillStyle = baseColor;
    ctx.fillRect(x, y, 32, 32);
    
    // 添加草地紋理
    ctx.fillStyle = darkColor;
    for (let i = 0; i < 12; i++) {
        const px = x + Math.random() * 32;
        const py = y + Math.random() * 32;
        const size = Math.random() > 0.5 ? 2 : 1;
        ctx.fillRect(px, py, size, size);
    }
    
    // 添加高光
    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
    for (let i = 0; i < 5; i++) {
        const px = x + Math.random() * 32;
        const py = y + Math.random() * 32;
        ctx.fillRect(px, py, 1, 1);
    }
}

function drawRoadTile(ctx, x, y, type = 'horizontal') {
    // 道路基礎
    ctx.fillStyle = CONFIG.colors.road;
    ctx.fillRect(x, y, 32, 32);
    
    // 道路紋理
    ctx.fillStyle = CONFIG.colors.roadDark;
    for (let i = 0; i < 8; i++) {
        const px = x + Math.random() * 32;
        const py = y + Math.random() * 32;
        ctx.fillRect(px, py, 1, 1);
    }
    
    // 道路標線
    ctx.fillStyle = CONFIG.colors.roadLine;
    if (type === 'horizontal') {
        ctx.fillRect(x, y + 14, 32, 4);
        // 虛線
        for (let i = 0; i < 32; i += 8) {
            ctx.fillRect(x + i, y + 15, 4, 2);
        }
    } else if (type === 'vertical') {
        ctx.fillRect(x + 14, y, 4, 32);
        for (let i = 0; i < 32; i += 8) {
            ctx.fillRect(x + 15, y + i, 2, 4);
        }
    }
}

function drawSidewalk(ctx, x, y) {
    ctx.fillStyle = CONFIG.colors.sidewalk;
    ctx.fillRect(x, y, 32, 32);
    
    // 人行道磚塊紋理
    ctx.strokeStyle = CONFIG.colors.sidewalkDark;
    ctx.lineWidth = 1;
    for (let i = 0; i < 32; i += 16) {
        ctx.strokeRect(x + i, y, 16, 16);
        ctx.strokeRect(x + i, y + 16, 16, 16);
    }
}

// ============================================================================
// 建築繪製函數
// ============================================================================

function drawBuilding(ctx, x, y, width, height, roofColor, style = 'modern') {
    // 陰影
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(x + 5, y + 25, width, height - 20);
    
    // 牆壁
    const wallGradient = ctx.createLinearGradient(x, y, x + width, y);
    wallGradient.addColorStop(0, CONFIG.colors.building);
    wallGradient.addColorStop(0.5, '#f5f5f5');
    wallGradient.addColorStop(1, CONFIG.colors.buildingDark);
    ctx.fillStyle = wallGradient;
    ctx.fillRect(x, y + 20, width, height - 20);
    
    // 牆壁陰影
    ctx.fillStyle = CONFIG.colors.buildingDark;
    ctx.fillRect(x, y + height - 10, width, 10);
    
    // 屋頂
    ctx.fillStyle = roofColor;
    ctx.beginPath();
    ctx.moveTo(x - 10, y + 20);
    ctx.lineTo(x + width / 2, y);
    ctx.lineTo(x + width + 10, y + 20);
    ctx.closePath();
    ctx.fill();
    
    // 屋頂陰影
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.beginPath();
    ctx.moveTo(x + width / 2, y);
    ctx.lineTo(x + width + 10, y + 20);
    ctx.lineTo(x - 10, y + 20);
    ctx.closePath();
    ctx.fill();
    
    // 窗戶
    const windowSize = 16;
    const windowSpacing = 24;
    const floors = Math.floor((height - 40) / windowSpacing);
    const windowsPerFloor = Math.floor((width - 40) / windowSpacing);
    
    for (let floor = 0; floor < floors; floor++) {
        for (let win = 0; win < windowsPerFloor; win++) {
            const wx = x + 20 + win * windowSpacing;
            const wy = y + 35 + floor * windowSpacing;
            
            // 窗戶玻璃
            const windowGradient = ctx.createLinearGradient(wx, wy, wx, wy + windowSize);
            windowGradient.addColorStop(0, CONFIG.colors.window);
            windowGradient.addColorStop(1, CONFIG.colors.windowDark);
            ctx.fillStyle = windowGradient;
            ctx.fillRect(wx, wy, windowSize, windowSize);
            
            // 窗框
            ctx.strokeStyle = '#424242';
            ctx.lineWidth = 2;
            ctx.strokeRect(wx, wy, windowSize, windowSize);
            
            // 窗戶十字
            ctx.beginPath();
            ctx.moveTo(wx + windowSize / 2, wy);
            ctx.lineTo(wx + windowSize / 2, wy + windowSize);
            ctx.moveTo(wx, wy + windowSize / 2);
            ctx.lineTo(wx + windowSize, wy + windowSize / 2);
            ctx.stroke();
            
            // 窗戶反光
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.fillRect(wx + 2, wy + 2, windowSize / 2 - 2, windowSize / 2 - 2);
        }
    }
    
    // 門
    const doorWidth = 24;
    const doorHeight = 36;
    const doorX = x + width / 2 - doorWidth / 2;
    const doorY = y + height - doorHeight - 5;
    
    ctx.fillStyle = CONFIG.colors.door;
    ctx.fillRect(doorX, doorY, doorWidth, doorHeight);
    ctx.fillStyle = CONFIG.colors.doorDark;
    ctx.fillRect(doorX, doorY, doorWidth, 4);
    ctx.fillRect(doorX, doorY + doorHeight - 4, doorWidth, 4);
    
    // 門把
    ctx.fillStyle = '#ffd700';
    ctx.fillRect(doorX + doorWidth - 6, doorY + doorHeight / 2, 3, 6);
}

// ============================================================================
// 裝飾物繪製函數
// ============================================================================

function drawTree(ctx, x, y, size = 1) {
    const scale = size;
    
    // 樹幹陰影
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(x - 4 * scale, y + 12 * scale, 8 * scale, 20 * scale);
    
    // 樹幹
    const trunkGradient = ctx.createLinearGradient(x - 5 * scale, y, x + 5 * scale, y);
    trunkGradient.addColorStop(0, '#6d4c41');
    trunkGradient.addColorStop(0.5, CONFIG.colors.trunk);
    trunkGradient.addColorStop(1, '#5d4037');
    ctx.fillStyle = trunkGradient;
    ctx.fillRect(x - 5 * scale, y + 10 * scale, 10 * scale, 25 * scale);
    
    // 樹幹紋理
    ctx.fillStyle = '#5d4037';
    for (let i = 0; i < 3; i++) {
        ctx.fillRect(x - 4 * scale, y + (15 + i * 5) * scale, 8 * scale, 2 * scale);
    }
    
    // 樹葉（多層）
    const layers = [
        { radius: 20 * scale, y: y, color: CONFIG.colors.tree },
        { radius: 16 * scale, y: y - 5 * scale, color: CONFIG.colors.treeLight },
        { radius: 12 * scale, y: y - 8 * scale, color: CONFIG.colors.treeDark }
    ];
    
    layers.forEach(layer => {
        ctx.fillStyle = layer.color;
        ctx.beginPath();
        ctx.arc(x, layer.y, layer.radius, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // 樹葉高光
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.beginPath();
    ctx.arc(x - 5 * scale, y - 5 * scale, 8 * scale, 0, Math.PI * 2);
    ctx.fill();
}

function drawFlower(ctx, x, y) {
    // 莖
    ctx.fillStyle = '#7cb342';
    ctx.fillRect(x + 2, y + 4, 2, 8);
    
    // 花瓣
    const petalColor = getRandomColor(CONFIG.colors.flower);
    ctx.fillStyle = petalColor;
    const petalPositions = [
        [x, y], [x + 4, y], [x, y + 4], [x + 4, y + 4]
    ];
    petalPositions.forEach(([px, py]) => {
        ctx.fillRect(px, py, 3, 3);
    });
    
    // 花心
    ctx.fillStyle = '#ffeb3b';
    ctx.fillRect(x + 1.5, y + 1.5, 3, 3);
}

function drawBench(ctx, x, y) {
    // 長椅腿
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(x, y + 8, 3, 8);
    ctx.fillRect(x + 13, y + 8, 3, 8);
    
    // 長椅座位
    ctx.fillStyle = '#a1887f';
    ctx.fillRect(x - 2, y + 6, 20, 4);
    
    // 長椅靠背
    ctx.fillRect(x, y, 16, 3);
    ctx.fillRect(x, y, 3, 8);
    ctx.fillRect(x + 13, y, 3, 8);
}

function drawStreetLight(ctx, x, y) {
    // 燈柱
    ctx.fillStyle = '#424242';
    ctx.fillRect(x + 6, y + 8, 3, 24);
    
    // 燈柱底座
    ctx.fillStyle = '#616161';
    ctx.fillRect(x + 4, y + 30, 7, 4);
    
    // 燈罩
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.arc(x + 7.5, y + 6, 6, 0, Math.PI * 2);
    ctx.fill();
    
    // 燈光效果
    ctx.fillStyle = 'rgba(255, 215, 0, 0.3)';
    ctx.beginPath();
    ctx.arc(x + 7.5, y + 6, 10, 0, Math.PI * 2);
    ctx.fill();
}

// ============================================================================
// 主地圖生成函數
// ============================================================================

async function generateProfessionalMap() {
    const loading = document.getElementById('loading');
    const previewSection = document.getElementById('previewSection');
    const successMsg = document.getElementById('successMsg');
    const mapContainer = document.getElementById('mapContainer');
    const infoPanel = document.getElementById('infoPanel');
    
    loading.style.display = 'block';
    previewSection.style.display = 'none';
    successMsg.style.display = 'none';
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 獲取配置
    const sizeStr = document.getElementById('mapSize').value;
    const [width, height] = sizeStr.split('x').map(Number);
    const detailLevel = document.getElementById('detailLevel').value;
    const buildingCount = parseInt(document.getElementById('buildingCount').value);
    const decorationDensity = document.getElementById('decorationDensity').value;
    
    // 創建畫布
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext('2d');
    
    // 1. 繪製草地背景
    console.log('繪製草地背景...');
    for (let y = 0; y < height; y += 32) {
        for (let x = 0; x < width; x += 32) {
            const variant = Math.floor(Math.random() * 4);
            drawGrassTile(ctx, x, y, variant);
        }
    }
    
    // 2. 繪製道路系統
    console.log('繪製道路系統...');
    drawRoadSystem(ctx, width, height);
    
    // 3. 繪製建築
    console.log('繪製建築...');
    drawBuildings(ctx, width, height, buildingCount);
    
    // 4. 繪製裝飾
    console.log('繪製裝飾...');
    const decorationCount = decorationDensity === 'high' ? 100 : decorationDensity === 'ultra' ? 150 : 60;
    drawDecorations(ctx, width, height, decorationCount);
    
    // 5. 添加標題
    drawMapTitle(ctx, width, '香港反詐騙訓練區');
    
    currentMap = canvas;
    
    // 顯示預覽
    mapContainer.innerHTML = '';
    mapContainer.appendChild(canvas);
    
    // 顯示信息
    infoPanel.innerHTML = `
        <div class="info-card"><strong>地圖尺寸</strong>${width} x ${height} 像素</div>
        <div class="info-card"><strong>建築數量</strong>${buildingCount} 棟</div>
        <div class="info-card"><strong>裝飾數量</strong>${decorationCount} 個</div>
        <div class="info-card"><strong>細節等級</strong>${detailLevel === 'ultra' ? '超高' : '高'}</div>
    `;
    
    loading.style.display = 'none';
    previewSection.style.display = 'block';
    successMsg.style.display = 'block';
    document.getElementById('mapInfo').textContent = 
        `地圖尺寸: ${width}x${height} | 建築: ${buildingCount}棟 | 裝飾: ${decorationCount}個`;
}

function drawRoadSystem(ctx, width, height) {
    const roadWidth = 64;
    
    // 主要水平道路
    for (let y = height / 4; y < height; y += height / 4) {
        for (let x = 0; x < width; x += 32) {
            drawRoadTile(ctx, x, y - 32, 'horizontal');
            drawRoadTile(ctx, x, y, 'horizontal');
        }
        // 人行道
        for (let x = 0; x < width; x += 32) {
            drawSidewalk(ctx, x, y - 64);
            drawSidewalk(ctx, x, y + 32);
        }
    }
    
    // 主要垂直道路
    for (let x = width / 4; x < width; x += width / 4) {
        for (let y = 0; y < height; y += 32) {
            drawRoadTile(ctx, x - 32, y, 'vertical');
            drawRoadTile(ctx, x, y, 'vertical');
        }
        // 人行道
        for (let y = 0; y < height; y += 32) {
            drawSidewalk(ctx, x - 64, y);
            drawSidewalk(ctx, x + 32, y);
        }
    }
}

function drawBuildings(ctx, width, height, count) {
    const roofColors = [
        CONFIG.colors.roofRed,
        CONFIG.colors.roofBlue,
        CONFIG.colors.roofOrange,
        CONFIG.colors.roofGreen,
        CONFIG.colors.roofPurple
    ];
    
    const buildings = [];
    for (let i = 0; i < count; i++) {
        const bWidth = 120 + Math.random() * 100;
        const bHeight = 100 + Math.random() * 80;
        const bX = Math.random() * (width - bWidth - 100) + 50;
        const bY = Math.random() * (height - bHeight - 100) + 50;
        const roofColor = roofColors[Math.floor(Math.random() * roofColors.length)];
        
        buildings.push({ x: bX, y: bY, width: bWidth, height: bHeight, roofColor });
    }
    
    // 按 Y 座標排序（遠近效果）
    buildings.sort((a, b) => a.y - b.y);
    
    buildings.forEach(b => {
        drawBuilding(ctx, b.x, b.y, b.width, b.height, b.roofColor);
    });
}

function drawDecorations(ctx, width, height, count) {
    for (let i = 0; i < count; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        const type = Math.random();
        
        if (type < 0.4) {
            drawTree(ctx, x, y, 0.8 + Math.random() * 0.4);
        } else if (type < 0.7) {
            drawFlower(ctx, x, y);
        } else if (type < 0.85) {
            drawBench(ctx, x, y);
        } else {
            drawStreetLight(ctx, x, y);
        }
    }
}

function drawMapTitle(ctx, width, title) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(width / 2 - 250, 20, 500, 60);
    
    ctx.fillStyle = '#ffd700';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 4;
    ctx.strokeText(title, width / 2, 60);
    ctx.fillText(title, width / 2, 60);
}

function downloadMap() {
    if (!currentMap) {
        alert('請先生成地圖！');
        return;
    }
    
    currentMap.toBlob(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'professional-world-map.png';
        a.click();
        URL.revokeObjectURL(url);
    }, 'image/png');
    
    alert('✅ 專業地圖已下載！\n\n請將檔案放到: public/assets/maps/');
}

function generateTileset() {
    alert('瓦片集生成功能開發中...\n\n目前請使用 generate-rpg-assets.html 生成瓦片集。');
}
