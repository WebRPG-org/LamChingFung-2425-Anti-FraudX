// RPG Maker 風格素材生成器
// 高品質像素藝術生成

const assets = [];

// ============================================================================
// 工具函數
// ============================================================================

function createCanvas(width, height) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    return canvas;
}

function drawPixel(ctx, x, y, color, size = 1) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, size, size);
}

function drawOutline(ctx, x, y, width, height, color = '#000') {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, width, height);
}

// ============================================================================
// 角色精靈生成器 (RPG Maker 風格 - 32x32)
// ============================================================================

function generatePlayerSprite() {
    const canvas = createCanvas(96, 128); // 3列4行的角色動畫
    const ctx = canvas.getContext('2d');
    
    const colors = {
        skin: '#fdbcb4',
        skinDark: '#f4a7a0',
        hair: '#8b4513',
        hairDark: '#654321',
        shirt: '#4a90e2',
        shirtDark: '#2e5c8a',
        pants: '#2c3e50',
        pantsDark: '#1a252f',
        shoes: '#34495e'
    };
    
    // 繪製 4 個方向 x 3 幀動畫
    const directions = ['down', 'left', 'right', 'up'];
    
    directions.forEach((dir, row) => {
        for (let frame = 0; frame < 3; frame++) {
            const x = frame * 32;
            const y = row * 32;
            drawCharacter(ctx, x, y, colors, dir, frame);
        }
    });
    
    return { canvas, name: 'player-spritesheet.png', folder: 'sprites', size: '96x128' };
}

function drawCharacter(ctx, offsetX, offsetY, colors, direction, frame) {
    const x = offsetX + 16;
    const y = offsetY + 16;
    
    // 頭部
    ctx.fillStyle = colors.skin;
    ctx.fillRect(x - 4, y - 8, 8, 8);
    ctx.fillStyle = colors.skinDark;
    ctx.fillRect(x - 4, y - 2, 8, 2);
    
    // 頭髮
    ctx.fillStyle = colors.hair;
    ctx.fillRect(x - 5, y - 10, 10, 4);
    ctx.fillStyle = colors.hairDark;
    ctx.fillRect(x - 5, y - 10, 10, 2);
    
    // 眼睛
    ctx.fillStyle = '#000';
    if (direction === 'down' || direction === 'up') {
        ctx.fillRect(x - 3, y - 5, 2, 1);
        ctx.fillRect(x + 1, y - 5, 2, 1);
    } else if (direction === 'left') {
        ctx.fillRect(x - 3, y - 5, 2, 1);
    } else if (direction === 'right') {
        ctx.fillRect(x + 1, y - 5, 2, 1);
    }
    
    // 身體
    ctx.fillStyle = colors.shirt;
    ctx.fillRect(x - 5, y - 2, 10, 8);
    ctx.fillStyle = colors.shirtDark;
    ctx.fillRect(x - 5, y + 4, 10, 2);
    
    // 手臂動畫
    const armOffset = frame === 1 ? 1 : (frame === 2 ? -1 : 0);
    ctx.fillStyle = colors.skin;
    ctx.fillRect(x - 7, y + armOffset, 2, 6);
    ctx.fillRect(x + 5, y - armOffset, 2, 6);
    
    // 褲子
    ctx.fillStyle = colors.pants;
    ctx.fillRect(x - 4, y + 6, 3, 6);
    ctx.fillRect(x + 1, y + 6, 3, 6);
    ctx.fillStyle = colors.pantsDark;
    ctx.fillRect(x - 4, y + 10, 3, 2);
    ctx.fillRect(x + 1, y + 10, 3, 2);
    
    // 腳部動畫
    const legOffset = frame === 1 ? 1 : (frame === 2 ? -1 : 0);
    ctx.fillStyle = colors.shoes;
    ctx.fillRect(x - 4, y + 12 + legOffset, 3, 2);
    ctx.fillRect(x + 1, y + 12 - legOffset, 3, 2);
}

// ============================================================================
// NPC 精靈生成器
// ============================================================================

function generateNPCSprites() {
    const npcs = [
        { 
            name: 'npc-scammer.png',
            colors: {
                skin: '#fdbcb4',
                skinDark: '#f4a7a0',
                hair: '#2c3e50',
                hairDark: '#1a252f',
                shirt: '#e74c3c',
                shirtDark: '#c0392b',
                pants: '#34495e',
                pantsDark: '#2c3e50',
                shoes: '#000'
            },
            hat: true
        },
        {
            name: 'npc-expert.png',
            colors: {
                skin: '#fdbcb4',
                skinDark: '#f4a7a0',
                hair: '#95a5a6',
                hairDark: '#7f8c8d',
                shirt: '#3498db',
                shirtDark: '#2980b9',
                pants: '#2c3e50',
                pantsDark: '#1a252f',
                shoes: '#34495e'
            },
            glasses: true
        },
        {
            name: 'npc-victim.png',
            colors: {
                skin: '#fdbcb4',
                skinDark: '#f4a7a0',
                hair: '#ecf0f1',
                hairDark: '#bdc3c7',
                shirt: '#f39c12',
                shirtDark: '#d68910',
                pants: '#7f8c8d',
                pantsDark: '#5d6d7e',
                shoes: '#95a5a6'
            },
            elderly: true
        }
    ];
    
    return npcs.map(npc => {
        const canvas = createCanvas(96, 128);
        const ctx = canvas.getContext('2d');
        
        const directions = ['down', 'left', 'right', 'up'];
        directions.forEach((dir, row) => {
            for (let frame = 0; frame < 3; frame++) {
                const x = frame * 32;
                const y = row * 32;
                drawNPCCharacter(ctx, x, y, npc.colors, dir, frame, npc);
            }
        });
        
        return { canvas, name: npc.name, folder: 'sprites', size: '96x128' };
    });
}

function drawNPCCharacter(ctx, offsetX, offsetY, colors, direction, frame, options) {
    drawCharacter(ctx, offsetX, offsetY, colors, direction, frame);
    
    const x = offsetX + 16;
    const y = offsetY + 16;
    
    // 添加特殊裝飾
    if (options.hat) {
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(x - 6, y - 12, 12, 3);
        ctx.fillRect(x - 5, y - 14, 10, 2);
    }
    
    if (options.glasses) {
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 1;
        ctx.strokeRect(x - 4, y - 6, 3, 3);
        ctx.strokeRect(x + 1, y - 6, 3, 3);
        ctx.fillRect(x - 1, y - 5, 2, 1);
    }
    
    if (options.elderly) {
        // 拐杖
        ctx.fillStyle = '#8b4513';
        ctx.fillRect(x + 6, y + 2, 1, 10);
        ctx.fillRect(x + 5, y + 2, 2, 2);
    }
}

// ============================================================================
// 地圖瓦片生成器 (RPG Maker 風格)
// ============================================================================

function generateTileset() {
    const canvas = createCanvas(512, 512);
    const ctx = canvas.getContext('2d');
    
    const tileSize = 32;
    let tileX = 0, tileY = 0;
    
    // 草地瓦片 (多種變化)
    for (let i = 0; i < 4; i++) {
        drawGrassTile(ctx, tileX * tileSize, tileY * tileSize, i);
        tileX++;
    }
    
    // 道路瓦片
    tileX = 0; tileY = 1;
    for (let i = 0; i < 4; i++) {
        drawRoadTile(ctx, tileX * tileSize, tileY * tileSize, i);
        tileX++;
    }
    
    // 建築瓦片
    tileX = 0; tileY = 2;
    drawBuildingTiles(ctx, tileX * tileSize, tileY * tileSize);
    
    // 裝飾物
    tileX = 0; tileY = 6;
    drawDecorationTiles(ctx, tileX * tileSize, tileY * tileSize);
    
    return { canvas, name: 'tileset.png', folder: 'maps', size: '512x512' };
}

function drawGrassTile(ctx, x, y, variant) {
    const baseColors = ['#7cb342', '#8bc34a', '#9ccc65', '#aed581'];
    const darkColors = ['#689f38', '#7cb342', '#8bc34a', '#9ccc65'];
    
    ctx.fillStyle = baseColors[variant];
    ctx.fillRect(x, y, 32, 32);
    
    // 添加草地紋理
    ctx.fillStyle = darkColors[variant];
    for (let i = 0; i < 8; i++) {
        const px = x + Math.random() * 32;
        const py = y + Math.random() * 32;
        ctx.fillRect(px, py, 2, 2);
    }
}

function drawRoadTile(ctx, x, y, variant) {
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(x, y, 32, 32);
    
    ctx.fillStyle = '#6d4c41';
    if (variant === 0) { // 水平
        ctx.fillRect(x, y + 14, 32, 4);
    } else if (variant === 1) { // 垂直
        ctx.fillRect(x + 14, y, 4, 32);
    } else if (variant === 2) { // 十字路口
        ctx.fillRect(x, y + 14, 32, 4);
        ctx.fillRect(x + 14, y, 4, 32);
    }
    
    // 添加石頭紋理
    ctx.fillStyle = '#5d4037';
    for (let i = 0; i < 5; i++) {
        const px = x + Math.random() * 32;
        const py = y + Math.random() * 32;
        ctx.fillRect(px, py, 1, 1);
    }
}

function drawBuildingTiles(ctx, startX, startY) {
    // 建築牆壁
    ctx.fillStyle = '#bdbdbd';
    ctx.fillRect(startX, startY, 32, 32);
    ctx.fillStyle = '#9e9e9e';
    ctx.fillRect(startX, startY + 28, 32, 4);
    
    // 屋頂
    ctx.fillStyle = '#d32f2f';
    ctx.fillRect(startX + 32, startY, 32, 32);
    ctx.fillStyle = '#b71c1c';
    for (let i = 0; i < 32; i += 4) {
        ctx.fillRect(startX + 32, startY + i, 32, 2);
    }
    
    // 窗戶
    ctx.fillStyle = '#64b5f6';
    ctx.fillRect(startX + 64, startY, 32, 32);
    ctx.fillStyle = '#1976d2';
    ctx.fillRect(startX + 70, startY + 8, 8, 10);
    ctx.fillRect(startX + 82, startY + 8, 8, 10);
    
    // 門
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(startX + 96, startY, 32, 32);
    ctx.fillStyle = '#5d4037';
    ctx.fillRect(startX + 104, startY + 10, 16, 20);
    ctx.fillStyle = '#ffd700';
    ctx.fillRect(startX + 114, startY + 20, 2, 2);
}

function drawDecorationTiles(ctx, startX, startY) {
    // 樹
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(startX + 14, startY + 20, 4, 12);
    ctx.fillStyle = '#2e7d32';
    ctx.beginPath();
    ctx.arc(startX + 16, startY + 16, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1b5e20';
    ctx.beginPath();
    ctx.arc(startX + 16, startY + 16, 8, 0, Math.PI * 2);
    ctx.fill();
    
    // 花
    ctx.fillStyle = '#7cb342';
    ctx.fillRect(startX + 46, startY + 28, 4, 4);
    ctx.fillStyle = '#f44336';
    ctx.fillRect(startX + 46, startY + 24, 4, 4);
    ctx.fillStyle = '#ffeb3b';
    ctx.fillRect(startX + 48, startY + 26, 2, 2);
    
    // 石頭
    ctx.fillStyle = '#78909c';
    ctx.fillRect(startX + 68, startY + 24, 8, 6);
    ctx.fillStyle = '#546e7a';
    ctx.fillRect(startX + 68, startY + 24, 8, 2);
}

// ============================================================================
// 世界地圖生成器
// ============================================================================

function generateWorldMap() {
    const canvas = createCanvas(800, 600);
    const ctx = canvas.getContext('2d');
    
    // 背景 - 草地
    for (let y = 0; y < 600; y += 32) {
        for (let x = 0; x < 800; x += 32) {
            const variant = Math.floor(Math.random() * 4);
            drawGrassTile(ctx, x, y, variant);
        }
    }
    
    // 主要道路
    for (let x = 0; x < 800; x += 32) {
        drawRoadTile(ctx, x, 280, 0);
    }
    for (let y = 0; y < 600; y += 32) {
        drawRoadTile(ctx, 380, y, 1);
    }
    drawRoadTile(ctx, 380, 280, 2);
    
    // 建築物
    drawBuilding(ctx, 100, 100, 150, 120, '#d32f2f');
    drawBuilding(ctx, 550, 380, 150, 120, '#1976d2');
    drawBuilding(ctx, 500, 100, 120, 100, '#f57c00');
    
    // 裝飾
    drawTree(ctx, 250, 150);
    drawTree(ctx, 300, 180);
    drawTree(ctx, 650, 250);
    drawTree(ctx, 150, 450);
    
    // 標題
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(250, 10, 300, 50);
    ctx.fillStyle = '#ffd700';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('香港街道', 400, 45);
    
    return { canvas, name: 'world-map.png', folder: 'maps', size: '800x600' };
}

function drawBuilding(ctx, x, y, width, height, roofColor) {
    // 牆壁
    ctx.fillStyle = '#e0e0e0';
    ctx.fillRect(x, y + 20, width, height - 20);
    ctx.fillStyle = '#bdbdbd';
    ctx.fillRect(x, y + height - 10, width, 10);
    
    // 屋頂
    ctx.fillStyle = roofColor;
    ctx.beginPath();
    ctx.moveTo(x - 10, y + 20);
    ctx.lineTo(x + width / 2, y);
    ctx.lineTo(x + width + 10, y + 20);
    ctx.closePath();
    ctx.fill();
    
    // 窗戶
    const windowSize = 20;
    const windowSpacing = 30;
    for (let wy = y + 40; wy < y + height - 20; wy += windowSpacing) {
        for (let wx = x + 20; wx < x + width - 20; wx += windowSpacing) {
            ctx.fillStyle = '#64b5f6';
            ctx.fillRect(wx, wy, windowSize, windowSize);
            ctx.strokeStyle = '#1976d2';
            ctx.lineWidth = 2;
            ctx.strokeRect(wx, wy, windowSize, windowSize);
        }
    }
    
    // 門
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(x + width / 2 - 15, y + height - 40, 30, 40);
    ctx.fillStyle = '#ffd700';
    ctx.fillRect(x + width / 2 + 5, y + height - 25, 4, 4);
}

function drawTree(ctx, x, y) {
    // 樹幹
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(x - 5, y + 10, 10, 25);
    
    // 樹葉
    ctx.fillStyle = '#2e7d32';
    ctx.beginPath();
    ctx.arc(x, y, 20, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = '#388e3c';
    ctx.beginPath();
    ctx.arc(x - 8, y - 5, 15, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = '#43a047';
    ctx.beginPath();
    ctx.arc(x + 8, y - 5, 15, 0, Math.PI * 2);
    ctx.fill();
}

// ============================================================================
// UI 元素生成器
// ============================================================================

function generateDialogueBox() {
    const canvas = createCanvas(700, 180);
    const ctx = canvas.getContext('2d');
    
    // 外框陰影
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(5, 5, 690, 170);
    
    // 主體
    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, '#2c3e50');
    gradient.addColorStop(1, '#34495e');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 700, 180);
    
    // 內框
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 4;
    ctx.strokeRect(10, 10, 680, 160);
    
    // 裝飾邊框
    ctx.strokeStyle = '#ffd700';
    ctx.lineWidth = 2;
    ctx.strokeRect(15, 15, 670, 150);
    
    // 角落裝飾
    const corners = [[15, 15], [685, 15], [15, 165], [685, 165]];
    ctx.fillStyle = '#ffd700';
    corners.forEach(([x, y]) => {
        ctx.fillRect(x - 3, y - 3, 10, 10);
    });
    
    // 文字區域指示
    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.fillRect(30, 30, 640, 120);
    
    return { canvas, name: 'dialogue-box.png', folder: 'ui', size: '700x180' };
}

function generateButton() {
    const canvas = createCanvas(240, 70);
    const ctx = canvas.getContext('2d');
    
    // 陰影
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.roundRect(3, 3, 234, 64, 15);
    ctx.fill();
    
    // 按鈕主體
    const gradient = ctx.createLinearGradient(0, 0, 0, 70);
    gradient.addColorStop(0, '#667eea');
    gradient.addColorStop(0.5, '#764ba2');
    gradient.addColorStop(1, '#5a3d7a');
    ctx.fillStyle = gradient;
    ctx.roundRect(0, 0, 234, 64, 15);
    ctx.fill();
    
    // 高光
    const highlight = ctx.createLinearGradient(0, 0, 0, 30);
    highlight.addColorStop(0, 'rgba(255, 255, 255, 0.3)');
    highlight.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = highlight;
    ctx.roundRect(5, 5, 224, 25, 10);
    ctx.fill();
    
    // 邊框
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.roundRect(2, 2, 230, 60, 15);
    ctx.stroke();
    
    return { canvas, name: 'button.png', folder: 'ui', size: '240x70' };
}

function generateHealthBar() {
    const canvas = createCanvas(200, 30);
    const ctx = canvas.getContext('2d');
    
    // 背景
    ctx.fillStyle = '#2c3e50';
    ctx.fillRect(0, 0, 200, 30);
    
    // 邊框
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, 196, 26);
    
    // HP 條 (滿血狀態)
    const hpGradient = ctx.createLinearGradient(0, 0, 200, 0);
    hpGradient.addColorStop(0, '#e74c3c');
    hpGradient.addColorStop(1, '#c0392b');
    ctx.fillStyle = hpGradient;
    ctx.fillRect(5, 5, 190, 20);
    
    // 高光
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fillRect(5, 5, 190, 8);
    
    return { canvas, name: 'health-bar.png', folder: 'ui', size: '200x30' };
}

// ============================================================================
// 主要生成函數
// ============================================================================

async function generateAll() {
    const loading = document.getElementById('loading');
    const previewGrid = document.getElementById('previewGrid');
    const successMsg = document.getElementById('successMsg');
    
    loading.style.display = 'block';
    previewGrid.innerHTML = '';
    successMsg.style.display = 'none';
    assets.length = 0;
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 生成所有素材
    assets.push(generatePlayerSprite());
    assets.push(...generateNPCSprites());
    assets.push(generateTileset());
    assets.push(generateWorldMap());
    assets.push(generateDialogueBox());
    assets.push(generateButton());
    assets.push(generateHealthBar());
    
    // 顯示預覽
    assets.forEach(asset => {
        const card = document.createElement('div');
        card.className = 'preview-card';
        
        card.innerHTML = `
            <h3>📦 ${asset.name}</h3>
            <div class="canvas-container"></div>
            <div class="info">
                <strong>尺寸:</strong> ${asset.size}<br>
                <strong>資料夾:</strong> ${asset.folder}/
            </div>
        `;
        
        const container = card.querySelector('.canvas-container');
        const preview = asset.canvas.cloneNode(true);
        preview.style.maxWidth = '100%';
        container.appendChild(preview);
        
        previewGrid.appendChild(card);
    });
    
    loading.style.display = 'none';
    successMsg.style.display = 'block';
    document.getElementById('assetCount').textContent = assets.length;
}

function downloadAll() {
    if (assets.length === 0) {
        alert('請先點擊「生成所有素材」！');
        return;
    }
    
    assets.forEach((asset, index) => {
        setTimeout(() => {
            asset.canvas.toBlob(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = asset.name;
                a.click();
                URL.revokeObjectURL(url);
            }, 'image/png');
        }, index * 200);
    });
    
    setTimeout(() => {
        alert(`✅ 已開始下載 ${assets.length} 個高品質素材！\n\n` +
              `請將檔案放到以下位置：\n\n` +
              `• *-spritesheet.png → public/assets/sprites/\n` +
              `• tileset.png, world-map.png → public/assets/maps/\n` +
              `• dialogue-box.png, button.png, health-bar.png → public/assets/ui/\n\n` +
              `或使用 move-assets.ps1 腳本自動安裝`);
    }, 500);
}

function downloadIndividual() {
    if (assets.length === 0) {
        alert('請先點擊「生成所有素材」！');
        return;
    }
    alert('請在預覽中右鍵點擊圖片，選擇「另存圖片」來單獨下載。');
}

// 頁面載入時自動生成
window.addEventListener('load', () => {
    generateAll();
});

// 添加 roundRect 支援（舊版瀏覽器）
if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function(x, y, width, height, radius) {
        this.beginPath();
        this.moveTo(x + radius, y);
        this.lineTo(x + width - radius, y);
        this.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.lineTo(x + width, y + height - radius);
        this.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.lineTo(x + radius, y + height);
        this.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.lineTo(x, y + radius);
        this.quadraticCurveTo(x, y, x + radius, y);
        this.closePath();
    };
}
