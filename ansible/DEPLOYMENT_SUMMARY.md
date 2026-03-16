# Ansible 自動化部署 - 完成總結

## ✅ 已完成的功能

### 1. 目錄結構
```
ansible/
├── README.md                    # 完整文檔
├── QUICKSTART.md               # 快速開始指南
├── ansible.cfg                 # Ansible 配置
├── requirements.txt            # Python 依賴
├── deploy.sh                   # Linux/Mac 部署腳本
├── deploy.bat                  # Windows 部署腳本
├── inventory/
│   ├── hosts.yml              # 服務器清單
│   ├── hosts.example.yml      # 示例配置
│   └── group_vars/
│       └── all.yml            # 全局變量
├── playbooks/
│   ├── site.yml               # 完整部署
│   ├── frontend.yml           # 前端部署
│   ├── backend.yml            # 後端部署
│   ├── dev-setup.yml          # 開發環境
│   └── update.yml             # 更新應用
└── roles/
    ├── common/                # 基礎系統設置
    │   ├── tasks/main.yml
    │   └── handlers/main.yml
    ├── frontend/              # 前端部署
    │   ├── tasks/main.yml
    │   └── templates/
    │       ├── frontend.env.j2
    │       ├── frontend-pm2.config.js.j2
    │       └── frontend.service.j2
    ├── backend/               # 後端部署
    │   ├── tasks/main.yml
    │   └── templates/
    │       ├── backend.env.j2
    │       ├── gunicorn.conf.py.j2
    │       └── backend.service.j2
    └── nginx/                 # Web 服務器
        ├── tasks/main.yml
        ├── handlers/main.yml
        └── templates/
            ├── frontend-nginx.conf.j2
            └── backend-nginx.conf.j2
```

### 2. 核心功能

#### ✅ 自動化安裝
- Node.js 20.x
- Python 3.11
- Nginx
- PM2
- 系統依賴

#### ✅ 應用部署
- 前端（Vite + Phaser.js）
- 後端（Flask + OpenAI）
- 反向代理（Nginx）
- 進程管理（PM2 + Systemd）

#### ✅ 配置管理
- 環境變量
- 服務配置
- 日誌管理
- 防火牆規則

#### ✅ 多環境支持
- 生產環境
- 測試環境
- 開發環境

## 🚀 使用方法

### 快速部署（3 步驟）

```bash
# 1. 安裝 Ansible
pip install -r ansible/requirements.txt

# 2. 配置服務器
vim ansible/inventory/hosts.yml

# 3. 部署
cd ansible
./deploy.sh
```

### 常用命令

```bash
# 完整部署
./deploy.sh

# 只部署前端
./deploy.sh --frontend

# 只部署後端
./deploy.sh --backend

# 開發環境設置
./deploy.sh --dev

# 更新應用
./deploy.sh --update

# 檢查模式（不實際執行）
./deploy.sh --check

# 詳細輸出
./deploy.sh --verbose
```

## 📋 部署清單

### 在目標服務器上會安裝：

1. **系統軟件**
   - Git, curl, wget, vim, htop
   - Build tools
   - Node.js 20.x
   - Python 3.11
   - Nginx

2. **應用組件**
   - RPG 遊戲前端（端口 3000）
   - AI 後端 API（端口 5000）
   - PM2 進程管理
   - Systemd 服務

3. **配置文件**
   - `/opt/hk-antiscam-rpg/` - 應用目錄
   - `/var/log/hk-antiscam-rpg/` - 日誌目錄
   - `/etc/systemd/system/` - 服務配置
   - `/etc/nginx/sites-available/` - Nginx 配置

## 🔧 自定義配置

編輯 `inventory/group_vars/all.yml`：

```yaml
# 修改端口
frontend_port: 8080
backend_port: 8000

# 修改域名
frontend_domain: game.example.com
backend_domain: api.example.com

# 啟用 SSL
enable_ssl: true
ssl_cert_path: /etc/ssl/certs/game.crt
ssl_key_path: /etc/ssl/private/game.key

# 性能調優
pm2_instances: 4
gunicorn_workers: 8
```

## 📊 部署後驗證

```bash
# 檢查服務狀態
ansible all -i inventory/hosts.yml -m shell -a "systemctl status hk-antiscam-rpg-frontend"
ansible all -i inventory/hosts.yml -m shell -a "systemctl status hk-antiscam-rpg-backend"

# 檢查端口
ansible all -i inventory/hosts.yml -m shell -a "netstat -tlnp | grep -E '3000|5000'"

# 測試 HTTP 訪問
curl http://your-server-ip:3000
curl http://your-server-ip:5000/health
```

## 🔒 安全建議

1. **使用 SSH 密鑰**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id user@server
   ```

2. **使用 Ansible Vault 保護敏感數據**
   ```bash
   ansible-vault create inventory/group_vars/vault.yml
   ansible-vault encrypt_string 'secret_password' --name 'db_password'
   ```

3. **啟用防火牆**
   ```yaml
   enable_firewall: true
   allowed_ports:
     - 22
     - 80
     - 443
   ```

4. **配置 SSL/TLS**
   ```yaml
   enable_ssl: true
   ssl_cert_path: /path/to/cert.crt
   ssl_key_path: /path/to/key.key
   ```

## 📝 維護操作

### 更新應用
```bash
cd ansible
./deploy.sh --update
```

### 重啟服務
```bash
ansible all -i inventory/hosts.yml -m systemd -a "name=hk-antiscam-rpg-frontend state=restarted" --become
```

### 查看日誌
```bash
ansible all -i inventory/hosts.yml -m shell -a "tail -n 50 /var/log/hk-antiscam-rpg/frontend.log"
```

### 備份數據
```bash
ansible all -i inventory/hosts.yml -m shell -a "tar -czf /backup/app-$(date +%Y%m%d).tar.gz /opt/hk-antiscam-rpg" --become
```

## 🎯 下一步

1. **配置域名**
   - 設置 DNS A 記錄
   - 配置 Nginx 虛擬主機

2. **設置 SSL 證書**
   ```bash
   # 使用 Let's Encrypt
   sudo certbot --nginx -d game.example.com
   ```

3. **監控和告警**
   - 設置 Prometheus + Grafana
   - 配置日誌聚合（ELK Stack）

4. **自動化備份**
   - 配置定時備份任務
   - 設置異地備份

5. **CI/CD 集成**
   - 連接 GitHub Actions
   - 自動化測試和部署

## 📚 相關文檔

- [README.md](README.md) - 完整文檔
- [QUICKSTART.md](QUICKSTART.md) - 快速開始
- [Ansible 官方文檔](https://docs.ansible.com/)

## 💡 提示

- 首次部署建議使用 `--check` 模式測試
- 使用 `--verbose` 查看詳細執行過程
- 定期更新 Ansible 和依賴包
- 保持 playbooks 和 roles 的版本控制

## ✨ 特性

- ✅ 一鍵部署到多台服務器
- ✅ 支持 Linux/Mac/Windows
- ✅ 自動化依賴安裝
- ✅ 進程管理和自動重啟
- ✅ 日誌管理
- ✅ 防火牆配置
- ✅ Nginx 反向代理
- ✅ SSL/TLS 支持
- ✅ 多環境配置
- ✅ 滾動更新

---

**部署成功！** 🎉

現在你可以在多台電腦上自動安裝和部署香港反詐騙 RPG 訓練系統了！
