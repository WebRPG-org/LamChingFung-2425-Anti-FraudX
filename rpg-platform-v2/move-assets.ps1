# RPG Maker 風格素材自動安裝腳本
# 將下載的高品質素材移動到正確位置

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎨 RPG Maker 風格素材安裝工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 設定路徑
$downloadsPath = "$env:USERPROFILE\Downloads"
$projectRoot = $PSScriptRoot
$assetsRoot = Join-Path $projectRoot "public\assets"

Write-Host "📂 下載資料夾: " -NoNewline -ForegroundColor Yellow
Write-Host $downloadsPath
Write-Host "📂 目標資料夾: " -NoNewline -ForegroundColor Yellow
Write-Host $assetsRoot
Write-Host ""

# 定義素材映射（新版高品質素材）
$assetMappings = @{
    # 角色精靈圖
    "player-spritesheet.png" = "sprites"
    "npc-scammer.png" = "sprites"
    "npc-expert.png" = "sprites"
    "npc-victim.png" = "sprites"
    
    # 地圖素材
    "tileset.png" = "maps"
    "world-map.png" = "maps"
    
    # UI 元素
    "dialogue-box.png" = "ui"
    "button.png" = "ui"
    "health-bar.png" = "ui"
}

# 也支持舊版素材名稱
$legacyMappings = @{
    "player.png" = "sprites"
}

$allMappings = $assetMappings + $legacyMappings

$movedCount = 0
$notFoundCount = 0
$skippedCount = 0

Write-Host "🔍 開始搜尋並安裝素材..." -ForegroundColor Green
Write-Host ""

foreach ($fileName in $allMappings.Keys) {
    $sourcePath = Join-Path $downloadsPath $fileName
    $targetFolder = Join-Path $assetsRoot $allMappings[$fileName]
    $targetPath = Join-Path $targetFolder $fileName
    
    if (Test-Path $sourcePath) {
        try {
            # 確保目標資料夾存在
            if (-not (Test-Path $targetFolder)) {
                New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
                Write-Host "  📁 創建資料夾: $($allMappings[$fileName])/" -ForegroundColor Cyan
            }
            
            # 檢查目標檔案
            if (Test-Path $targetPath) {
                $sourceHash = (Get-FileHash $sourcePath -Algorithm MD5).Hash
                $targetHash = (Get-FileHash $targetPath -Algorithm MD5).Hash
                
                if ($sourceHash -eq $targetHash) {
                    Write-Host "  ⏭️  跳過 (已存在): $fileName" -ForegroundColor Gray
                    $skippedCount++
                    continue
                } else {
                    Remove-Item $targetPath -Force
                    Write-Host "  🔄 更新現有檔案: $fileName" -ForegroundColor Yellow
                }
            }
            
            # 移動檔案
            Move-Item -Path $sourcePath -Destination $targetPath -Force
            Write-Host "  ✅ 已安裝: $fileName → $($allMappings[$fileName])/" -ForegroundColor Green
            $movedCount++
        }
        catch {
            Write-Host "  ❌ 安裝失敗: $fileName" -ForegroundColor Red
            Write-Host "     錯誤: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        if ($assetMappings.ContainsKey($fileName)) {
            Write-Host "  ⚠️  找不到: $fileName" -ForegroundColor Yellow
            $notFoundCount++
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  📊 安裝結果統計" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ✅ 成功安裝: " -NoNewline -ForegroundColor Green
Write-Host "$movedCount 個檔案"
Write-Host "  ⏭️  已存在跳過: " -NoNewline -ForegroundColor Gray
Write-Host "$skippedCount 個檔案"
Write-Host "  ⚠️  找不到: " -NoNewline -ForegroundColor Yellow
Write-Host "$notFoundCount 個檔案"
Write-Host ""

$totalExpected = $assetMappings.Count
$totalInstalled = $movedCount + $skippedCount

if ($totalInstalled -eq $totalExpected) {
    Write-Host "🎉 完美！所有素材已成功安裝！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 素材清單:" -ForegroundColor Cyan
    Write-Host "  • 角色精靈圖: 4 個 (player + 3 NPCs)" -ForegroundColor White
    Write-Host "  • 地圖素材: 2 個 (tileset + world-map)" -ForegroundColor White
    Write-Host "  • UI 元素: 3 個 (dialogue-box + button + health-bar)" -ForegroundColor White
    Write-Host ""
    Write-Host "🎮 下一步:" -ForegroundColor Cyan
    Write-Host "  1. 訪問 http://localhost:3000/ 查看遊戲" -ForegroundColor White
    Write-Host "  2. 使用 WASD 或方向鍵移動角色" -ForegroundColor White
    Write-Host "  3. 按空白鍵與 NPC 互動" -ForegroundColor White
    Write-Host "  4. 按 ESC 返回主選單" -ForegroundColor White
}
elseif ($totalInstalled -gt 0) {
    Write-Host "⚠️  部分素材已安裝 ($totalInstalled/$totalExpected)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "缺少的素材:" -ForegroundColor Yellow
    foreach ($fileName in $assetMappings.Keys) {
        $targetPath = Join-Path (Join-Path $assetsRoot $assetMappings[$fileName]) $fileName
        if (-not (Test-Path $targetPath)) {
            Write-Host "  • $fileName" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "💡 解決方案:" -ForegroundColor Cyan
    Write-Host "  1. 打開 generate-rpg-assets.html" -ForegroundColor White
    Write-Host "  2. 點擊「💾 下載所有素材」按鈕" -ForegroundColor White
    Write-Host "  3. 等待所有檔案下載完成" -ForegroundColor White
    Write-Host "  4. 再次運行此腳本" -ForegroundColor White
}
else {
    Write-Host "❌ 沒有找到任何素材檔案！" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 請按照以下步驟操作:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  步驟 1: 生成素材" -ForegroundColor Yellow
    Write-Host "    • 打開 generate-rpg-assets.html" -ForegroundColor White
    Write-Host "    • 或在瀏覽器訪問: file:///$projectRoot/generate-rpg-assets.html" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  步驟 2: 下載素材" -ForegroundColor Yellow
    Write-Host "    • 點擊「💾 下載所有素材」按鈕" -ForegroundColor White
    Write-Host "    • 等待 9 個檔案下載完成" -ForegroundColor White
    Write-Host ""
    Write-Host "  步驟 3: 安裝素材" -ForegroundColor Yellow
    Write-Host "    • 再次運行此腳本: .\move-assets.ps1" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查開發伺服器是否運行
$viteProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*vite*"
}

if ($viteProcess) {
    Write-Host "✅ Vite 開發伺服器正在運行" -ForegroundColor Green
    Write-Host "   訪問: http://localhost:3000/" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  開發伺服器未運行" -ForegroundColor Yellow
    Write-Host "   啟動命令: npm run dev" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
