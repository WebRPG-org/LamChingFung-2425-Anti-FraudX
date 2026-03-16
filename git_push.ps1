#!/usr/bin/env pwsh
# Git initialization and push script

$projectPath = "C:\Users\andy1\Desktop\新增資料夾 (2)\AI-Agent-main v9-3-11-26\AI-Agent-main"

# Change to project directory
Push-Location $projectPath

try {
    Write-Host "Initializing Git repository..." -ForegroundColor Green
    git init
    
    Write-Host "Configuring Git user..." -ForegroundColor Green
    git config user.name "Andy"
    git config user.email "240302611@stu.vtc.edu.hk"
    
    Write-Host "Adding files..." -ForegroundColor Green
    git add .
    
    Write-Host "Creating initial commit..." -ForegroundColor Green
    git commit -m "Initial commit"
    
    Write-Host "Adding remote origin..." -ForegroundColor Green
    git remote add origin https://github.com/LamChingFung-2425/AI-Agent.git
    
    Write-Host "Renaming branch to andy-v8..." -ForegroundColor Green
    git branch -M andy-v8
    
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    git push -u origin andy-v8
    
    Write-Host "Done! Your code has been pushed to GitHub." -ForegroundColor Green
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
finally {
    Pop-Location
}

