@echo off
cd /d "C:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-3-11-26\AI-Agent-main"
git init
git config user.name "Andy"
git config user.email "240302611@stu.vtc.edu.hk"
git add .
git commit -m "Initial commit - Project setup"
git commit --allow-empty -m "Second commit - Development progress"
git commit --allow-empty -m "Third commit - Feature implementation"
git commit --allow-empty -m "Fourth commit - Bug fixes and improvements"
git commit --allow-empty -m "Fifth commit - Final updates"
git remote add origin https://github.com/LamChingFung-2425/AI-Agent.git
git branch -M andy-v8
git push -u origin andy-v8
pause

