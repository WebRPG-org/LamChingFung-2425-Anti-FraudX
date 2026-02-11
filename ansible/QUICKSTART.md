# Quick Start Guide - Ansible Deployment

## 快速開始指南

### 1. 準備工作

#### 在控制機器上（你的電腦）

```bash
# 安裝 Ansible
pip install ansible

# 或在 Windows 上使用 WSL
wsl --install
# 然後在 WSL 中安裝 Ansible
```

#### 在目標機器上

確保目標機器滿足以下條件：
- ✅ SSH 訪問已啟用
- ✅ Python 3.8+ 已安裝
- ✅ 有 sudo 權限的用戶

### 2. 配置清單（Inventory）

編輯 `inventory/hosts.yml`，添加你的服務器：

```yaml
all:
  children:
    game_servers:
      hosts:
        server1:
          ansible_host: 192.168.1.10  # 改成你的服務器 IP
          ansible_user: ubuntu         # 改成你的用戶名
```

### 3. 測試連接

```bash
# 測試所有服務器連接
ansible all -i inventory/hosts.yml -m ping

# 如果需要密碼
ansible all -i inventory/hosts.yml -m ping --ask-pass
```

### 4. 部署應用

#### 方法 A：使用部署腳本（推薦）

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh                    # 完整部署
./deploy.sh --frontend         # 只部署前端
./deploy.sh --backend          # 只部署後端
./deploy.sh --dev              # 開發環境設置
./deploy.sh --check            # 檢查模式（不實際執行）
```

**Windows:**
```cmd
deploy.bat                     # 完整部署
deploy.bat --frontend          # 只部署前端
deploy.bat --backend           # 只部署後端
deploy.bat --dev               # 開發環境設置
```

#### 方法 B：直接使用 Ansible

```bash
# 完整部署（前端 + 後端 + Nginx）
ansible-playbook -i inventory/hosts.yml playbooks/site.yml

# 只部署前端
ansible-playbook -i inventory/hosts.yml playbooks/frontend.yml

# 只部署後端
ansible-playbook -i inventory/hosts.yml playbooks/backend.yml

# 開發環境設置
ansible-playbook -i inventory/hosts.yml playbooks/dev-setup.yml

# 更新現有安裝
ansible-playbook -i inventory/hosts.yml playbooks/update.yml
```

### 5. 驗證部署

部署完成後，訪問：

- **前端**: http://your-server-ip:3000
- **後端 API**: http://your-server-ip:5000/health

### 6. 常見場景

#### 場景 1：部署到單台服務器

```bash
# 1. 配置 inventory
vim inventory/hosts.yml

# 2. 部署
./deploy.sh

# 3. 訪問
# http://your-server-ip:3000
```

#### 場景 2：部署到多台服務器

```bash
# 部署到所有服務器
ansible-playbook -i inventory/hosts.yml playbooks/site.yml

# 只部署到特定服務器
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --limit server1
```

#### 場景 3：開發環境設置

```bash
# 在本地機器設置開發環境
./deploy.sh --dev

# 或指定開發機器
ansible-playbook -i inventory/hosts.yml playbooks/dev-setup.yml --limit dev-1
```

#### 場景 4：更新應用

```bash
# 更新所有組件
./deploy.sh --update

# 或
ansible-playbook -i inventory/hosts.yml playbooks/update.yml
```

### 7. 自定義配置

編輯 `inventory/group_vars/all.yml` 來自定義設置：

```yaml
# 修改端口
frontend_port: 8080
backend_port: 8000

# 修改域名
frontend_domain: game.example.com
backend_domain: api.example.com

# 啟用 SSL
enable_ssl: true
```

### 8. 故障排除

#### SSH 連接問題

```bash
# 測試連接
ansible all -i inventory/hosts.yml -m ping

# 使用密碼認證
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --ask-pass

# 使用 sudo 密碼
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --ask-become-pass
```

#### 查看詳細日誌

```bash
# 詳細輸出
ansible-playbook -i inventory/hosts.yml playbooks/site.yml -vvv
```

#### 檢查模式（不實際執行）

```bash
# 查看會做什麼改變
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --check
```

### 9. 服務管理

部署後，在目標服務器上：

```bash
# 查看服務狀態
sudo systemctl status hk-antiscam-rpg-frontend
sudo systemctl status hk-antiscam-rpg-backend

# 重啟服務
sudo systemctl restart hk-antiscam-rpg-frontend
sudo systemctl restart hk-antiscam-rpg-backend

# 查看日誌
sudo journalctl -u hk-antiscam-rpg-frontend -f
sudo journalctl -u hk-antiscam-rpg-backend -f

# 或查看應用日誌
tail -f /var/log/hk-antiscam-rpg/frontend.log
tail -f /var/log/hk-antiscam-rpg/backend.log
```

### 10. 下一步

- 📝 配置域名 DNS
- 🔒 設置 SSL 證書（Let's Encrypt）
- 📊 設置監控和告警
- 💾 配置自動備份
- 🔥 配置防火牆規則

## 需要幫助？

查看完整文檔：`README.md`
