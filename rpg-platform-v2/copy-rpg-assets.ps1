# Copy RPG Maker MV Professional Assets
# From RPG_platform to rpg-platform-v2

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Copy Professional RPG Maker MV Assets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set paths
$sourceRoot = "C:\Users\fungr\Documents\AI-Agentv4\RPG_platform\RPG_Project"
$targetRoot = "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2\public\assets"

Write-Host "Source: $sourceRoot" -ForegroundColor Yellow
Write-Host "Target: $targetRoot" -ForegroundColor Yellow
Write-Host ""

# Check source directory
if (-not (Test-Path $sourceRoot)) {
    Write-Host "ERROR: Source directory not found!" -ForegroundColor Red
    exit 1
}

# Create target directories
$directories = @(
    "sprites",
    "maps", 
    "tilesets",
    "ui",
    "characters",
    "enemies",
    "battlebacks",
    "animations",
    "system"
)

Write-Host "Creating target folders..." -ForegroundColor Green
foreach ($dir in $directories) {
    $targetDir = Join-Path $targetRoot $dir
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Write-Host "  Created: $dir/" -ForegroundColor Green
    }
}
Write-Host ""

# Copy asset mappings
$assetMappings = @{
    "img\characters\*.png" = "characters"
    "img\tilesets\*.png" = "tilesets"
    "img\battlebacks1\*.png" = "battlebacks"
    "img\battlebacks2\*.png" = "battlebacks"
    "img\enemies\*.png" = "enemies"
    "img\animations\*.png" = "animations"
    "img\system\*.png" = "system"
    "img\titles1\*.png" = "maps"
}

$copiedCount = 0
$totalSize = 0

Write-Host "Copying professional assets..." -ForegroundColor Green
Write-Host ""

foreach ($pattern in $assetMappings.Keys) {
    $sourcePath = Join-Path $sourceRoot $pattern
    $targetFolder = Join-Path $targetRoot $assetMappings[$pattern]
    
    $files = Get-ChildItem -Path $sourcePath -ErrorAction SilentlyContinue
    
    if ($files) {
        $categoryName = $pattern.Split('\')[1]
        Write-Host "  Copying $categoryName..." -ForegroundColor Cyan
        
        foreach ($file in $files) {
            $targetPath = Join-Path $targetFolder $file.Name
            
            try {
                Copy-Item -Path $file.FullName -Destination $targetPath -Force
                $copiedCount++
                $totalSize += $file.Length
                
                if ($copiedCount % 50 -eq 0) {
                    Write-Host "    Progress: $copiedCount files..." -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "    Failed: $($file.Name)" -ForegroundColor Yellow
            }
        }
        
        Write-Host "    Done: $categoryName ($($files.Count) files)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Copy Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Files copied: $copiedCount" -ForegroundColor Green
Write-Host "  Total size: $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""

# Show asset categories
Write-Host "Available asset categories:" -ForegroundColor Yellow
Write-Host ""

$categories = @(
    @{Name="Characters"; Path="characters"},
    @{Name="Tilesets"; Path="tilesets"},
    @{Name="Battle Backgrounds"; Path="battlebacks"},
    @{Name="Enemies"; Path="enemies"},
    @{Name="Animations"; Path="animations"},
    @{Name="System UI"; Path="system"}
)

foreach ($cat in $categories) {
    $path = Join-Path $targetRoot $cat.Path
    if (Test-Path $path) {
        $fileCount = (Get-ChildItem $path -File).Count
        Write-Host "  $($cat.Name): $fileCount files" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Assets copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Check public/assets/ folders" -ForegroundColor White
Write-Host "  2. Load assets in Phaser" -ForegroundColor White
Write-Host "  3. Start developing!" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
