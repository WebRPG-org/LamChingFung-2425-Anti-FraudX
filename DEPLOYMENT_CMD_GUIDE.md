# Anti-FraudX 部署指南 - Windows CMD.exe 版本

## 📋 目錄

1. [第一階段：GCP 準備](#第一階段gcp-準備)
2. [第二階段：代碼遷移](#第二階段代碼遷移)
3. [第三階段：容器化](#第三階段容器化)
4. [第四階段：後端部署](#第四階段後端部署)
5. [第五階段：前端部署](#第五階段前端部署)
6. [第六階段：域名配置](#第六階段域名配置)
7. [第七階段：監控設置](#第七階段監控設置)
8. [第八階段：測試上線](#第八階段測試上線)

---

## 第一階段：GCP 準備 - CMD.exe 版本

### ✅ 已完成的步驟

- ✅ 初始化 gcloud
- ✅ 設置項目為 anti-fraudx
- ✅ 創建服務帳戶 anti-fraudx-sa
- ✅ 授予服務帳戶角色
- ✅ 創建服務帳戶密鑰
- ✅ 配置 Docker 認證
- ✅ 創建 Firestore 數據庫 anti-fraudx-db

### 步驟 1.1：創建 Cloud Storage 存儲桶

```cmd
REM 創建存儲桶
gsutil mb -l us-central1 gs://anti-fraudx-storage

REM 設置存儲桶權限
gsutil iam ch serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com:objectAdmin gs://anti-fraudx-storage

REM 驗證存儲桶
gsutil ls
```

### 步驟 1.2：驗證所有 API 已啟用

```cmd
REM 驗證 API 已啟用
gcloud services list --enabled
```

---

## 第二階段：代碼遷移 - CMD.exe 版本

### 步驟 2.1：創建環境配置文件

#### 創建 `.env.local`

```cmd
REM 進入 backend 目錄
cd backend

REM 創建 .env.local 文件
(
echo # 部署環境
echo DEPLOYMENT_ENV=local
echo PROJECT_ID=anti-fraudx-local
echo.
echo # Gemini API 配置（本地用）
echo GEMINI_ENABLED=true
echo GEMINI_API_KEY=your_gemini_api_key_here
echo.
echo # Ollama 配置（本地備用）
echo OLLAMA_BASE_URL=http://localhost:11434
echo OLLAMA_ENABLED=false
echo.
echo # 數據庫配置
echo DATABASE_TYPE=sqlite
echo DATABASE_PATH=./anti_fraud_game.db
echo.
echo # 存儲配置
echo STORAGE_TYPE=local
echo STORAGE_PATH=./backend/uploads
echo.
echo # 應用配置
echo APP_ENV=development
echo DEBUG=true
echo LOG_LEVEL=INFO
) > .env.local
```

#### 創建 `.env.cloud`

```cmd
REM 創建 .env.cloud 文件
(
echo # 部署環境
echo DEPLOYMENT_ENV=cloud
echo PROJECT_ID=anti-fraudx
echo.
echo # GCP 配置
echo GCP_PROJECT_ID=anti-fraudx
echo GCP_LOCATION=us-central1
echo.
echo # Vertex AI 配置
echo USE_VERTEX_AI=true
echo VERTEX_AI_MODEL=gemini-3.1-flash
echo VERTEX_AI_TEMPERATURE=0.7
echo VERTEX_AI_TOP_P=0.95
echo VERTEX_AI_TOP_K=40
echo VERTEX_AI_MAX_TOKENS=2048
echo.
echo # Firestore 配置
echo DATABASE_TYPE=firestore
echo FIRESTORE_PROJECT_ID=anti-fraudx
echo FIRESTORE_DATABASE=anti-fraudx-db
echo.
echo # Cloud Storage 配置
echo STORAGE_TYPE=gcs
echo CLOUD_STORAGE_BUCKET=anti-fraudx-storage
echo.
echo # Cloud Run 配置
echo CLOUD_RUN_SERVICE=anti-fraudx-backend
echo CLOUD_RUN_REGION=us-central1
echo.
echo # 域名配置
echo DOMAIN_NAME=anti-fraudx.us.ci
echo.
echo # 應用配置
echo APP_ENV=production
echo DEBUG=false
echo LOG_LEVEL=WARNING
) > .env.cloud
```

### 步驟 2.2：驗證文件

```cmd
REM 檢查文件是否存在
dir .env.local
dir .env.cloud

REM 查看文件內容
type .env.local
type .env.cloud
```

### 步驟 2.3：驗證 Vertex AI LLM 模塊

```cmd
REM 檢查文件是否存在
if exist llms\vertex_ai_llm.py (
    echo ✓ vertex_ai_llm.py 存在
) else (
    echo ✗ vertex_ai_llm.py 不存在，需要創建
)

REM 檢查 LLM Factory
if exist llms\llm_factory.py (
    echo ✓ llm_factory.py 存在
) else (
    echo ✗ llm_factory.py 不存在
)
```

### 步驟 2.4：本地測試 Vertex AI 連接

```cmd
REM 設置認證環境變量
set GOOGLE_APPLICATION_CREDENTIALS=C:\Users\andy1\anti-fraudx-key.json

REM 設置環境變量
set DEPLOYMENT_ENV=cloud
set GCP_PROJECT_ID=anti-fraudx
set VERTEX_AI_MODEL=gemini-3.1-flash

REM 運行測試腳本
python tests/test_vertex_ai_connection.py

REM 驗證輸出
REM 應該看到：✅ Vertex AI 連接成功
```

---

## 第三階段：容器化 - CMD.exe 版本

### 步驟 3.1：構建容器鏡像

```cmd
REM 返回項目根目錄
cd ..

REM 設置環境變量
set PROJECT_ID=anti-fraudx
set REGION=us-central1
set IMAGE_NAME=anti-fraudx-backend
set IMAGE_TAG=latest
set IMAGE_URL=%REGION%-docker.pkg.dev/%PROJECT_ID%/anti-fraudx-repo/%IMAGE_NAME%:%IMAGE_TAG%

REM 構建鏡像
docker build -f Dockerfile.cloud -t %IMAGE_URL% .

REM 驗證鏡像
docker images | findstr anti-fraudx-backend
```

### 步驟 3.2：推送到 Artifact Registry

```cmd
REM 推送鏡像
docker push %IMAGE_URL%

REM 驗證推送
gcloud artifacts docker images list us-central1-docker.pkg.dev/%PROJECT_ID%/anti-fraudx-repo
```

### 步驟 3.3：本地測試容器

```cmd
REM 運行容器
docker run -it ^
  -e DEPLOYMENT_ENV=cloud ^
  -e GCP_PROJECT_ID=%PROJECT_ID% ^
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json ^
  -v C:/Users/andy1/anti-fraudx-key.json:/app/key.json ^
  -p 8080:8080 ^
  %IMAGE_URL%

REM 在另一個 CMD 窗口測試健康檢查
curl http://localhost:8080/health

REM 停止容器
REM Ctrl+C
```

---

## 第四階段：後端部署 - CMD.exe 版本

### 步驟 4.1：部署到 Cloud Run

```cmd
REM 設置環境變量
set PROJECT_ID=anti-fraudx
set REGION=us-central1
set SERVICE_NAME=anti-fraudx-backend
set IMAGE_NAME=anti-fraudx-backend
set IMAGE_TAG=latest
set IMAGE_URL=%REGION%-docker.pkg.dev/%PROJECT_ID%/anti-fraudx-repo/%IMAGE_NAME%:%IMAGE_TAG%

REM 部署到 Cloud Run（單行）
gcloud run deploy %SERVICE_NAME% --image %IMAGE_URL% --platform managed --region %REGION% --memory 1Gi --cpu 2 --timeout 3600 --max-instances 10 --min-instances 0 --allow-unauthenticated --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=%PROJECT_ID%,VERTEX_AI_MODEL=gemini-2.5-flash-lite,GCP_LOCATION=%REGION%

REM 獲取服務 URL
gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)"
```

### 步驟 4.2：配置 IAM 權限

```cmd
set SERVICE_ACCOUNT=anti-fraudx-sa

REM 授予 Firestore 訪問權限
gcloud projects add-iam-policy-binding %PROJECT_ID% --member=serviceAccount:%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com --role=roles/datastore.user

REM 授予 Cloud Storage 訪問權限
gcloud projects add-iam-policy-binding %PROJECT_ID% --member=serviceAccount:%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com --role=roles/storage.objectAdmin

REM 授予 Vertex AI 訪問權限
gcloud projects add-iam-policy-binding %PROJECT_ID% --member=serviceAccount:%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com --role=roles/aiplatform.user
```

### 步驟 4.3：測試後端 API

```cmd
REM 獲取服務 URL
gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)"

REM 測試健康檢查
curl %SERVICE_URL%/health

REM 測試 API 端點
curl %SERVICE_URL%/test/json
```

---

## 第五階段：前端部署 - CMD.exe 版本

# 設置環境變量
$PROJECT_ID = "anti-fraudx"
$REGION = "us-central1"
$IMAGE_URL = "$REGION-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo/anti-fraudx-frontend:latest"

# 進入項目根目錄
cd "C:\Users\andy1\Desktop\新增資料夾 (2)\AI-Agent-main v9-3-11-26\AI-Agent-main"

# 構建 Docker 鏡像
docker build -t $IMAGE_URL -f Dockerfile.frontend .

# 推送到 Artifact Registry
docker push $IMAGE_URL

# 部署到 Cloud Run
gcloud run deploy anti-fraudx-frontend `
  --image $IMAGE_URL `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --port 8080 `
  --memory 512Mi `
  --cpu 1

# 獲取前端 URL
gcloud run services describe anti-fraudx-frontend --region $REGION --format="value(status.url)"

## 第六階段：域名配置 - CMD.exe 版本

### 步驟 6.1：創建 Cloud DNS 區域

```cmd
REM 設置環境變量
set DOMAIN=anti-fraudx.us.ci
set DNS_ZONE=anti-fraudx-us-ci


REM 創建 DNS 區域
gcloud dns managed-zones create %DNS_ZONE% --dns-name=%DOMAIN% --description="DNS zone for Anti-FraudX"


REM 獲取 DNS 名稱服務器
gcloud dns managed-zones describe %DNS_ZONE% --format="value(nameServers[])"

##FOR POWERSHELL###############
$DOMAIN = "anti-fraudx.us.ci"
$DNS_ZONE = "anti-fraudx-us-ci"

gcloud dns managed-zones create $DNS_ZONE --dns-name=$DOMAIN --description="DNS zone for Anti-FraudX"

gcloud dns managed-zones describe $DNS_ZONE --format="value(nameServers[])"
#################################

```

### 步驟 6.2：配置 DNS 記錄

```cmd
REM 獲取 Cloud Run 服務的 URL
gcloud run services describe anti-fraudx-backend --region us-central1 --format="value(status.url)"



REM 提取 IP（需要手動查詢或使用 nslookup）
REM nslookup <service-url>

REM 創建 A 記錄（指向 Cloud Run）
REM gcloud dns record-sets create %DOMAIN% --rrdatas=<CLOUD_RUN_IP> --ttl=300 --type=A --zone=%DNS_ZONE%

REM 創建 CNAME 記錄（指向 Cloud Storage）
gcloud dns record-sets create www.%DOMAIN% --rrdatas=c.storage.googleapis.com. --ttl=300 --type=CNAME --zone=%DNS_ZONE%

REM 驗證 DNS 記錄
gcloud dns record-sets list --zone=%DNS_ZONE%
```

### 步驟 6.3：申請 SSL 證書

```cmd
REM 使用 Google-managed SSL 證書
gcloud compute ssl-certificates create anti-fraudx-ssl-cert --domains=%DOMAIN%,www.%DOMAIN%

REM 驗證證書
gcloud compute ssl-certificates describe anti-fraudx-ssl-cert

REM 等待證書驗證（通常需要 15-30 分鐘）
```

### 步驟 6.4：驗證 HTTPS 連接

```cmd
REM 等待 DNS 傳播（通常 5-30 分鐘）
nslookup %DOMAIN%

REM 測試 HTTPS 連接
curl https://%DOMAIN%/health

REM 檢查 SSL 證書
openssl s_client -connect %DOMAIN%:443
```

---

## 第七階段：監控設置 - CMD.exe 版本

### 步驟 7.1：設置 Cloud Logging

```cmd
REM 設置環境變量
set PROJECT_ID=anti-fraudx

REM 創建日誌接收器
gcloud logging sinks create anti-fraudx-logs logging.googleapis.com/projects/%PROJECT_ID%/logs/anti-fraudx --log-filter="resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"anti-fraudx-backend\""

REM 查看日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=anti-fraudx-backend" --limit 50 --format json

REM 查看錯誤日誌
gcloud logging read "severity=ERROR" --limit 10
```

### 步驟 7.2：設置 Cloud Monitoring

```cmd
REM 驗證儀表板
gcloud monitoring dashboards list
```

---

## 第八階段：測試上線 - CMD.exe 版本

### 步驟 8.1：功能測試

```cmd
REM 設置環境變量
set DOMAIN=anti-fraudx.us.ci

REM 測試健康檢查
curl https://%DOMAIN%/health

REM 測試 API 端點
curl https://%DOMAIN%/test/json

REM 測試遊戲 API
curl https://%DOMAIN%/api/game/info
```

### 步驟 8.2：負載測試（30 人並發）

```cmd
REM 安裝負載測試工具
pip install locust

REM 創建負載測試腳本
(
echo from locust import HttpUser, task, between
echo.
echo class AntifraudxUser(HttpUser):
echo     wait_time = between(1, 3)
echo.
echo     @task
echo     def health_check(self):
echo         self.client.get("/health")
echo.
echo     @task
echo     def test_api(self):
echo         self.client.get("/test/json")
echo.
echo     @task
echo     def game_info(self):
echo         self.client.get("/api/game/info")
) > locustfile.py

REM 運行負載測試
locust -f locustfile.py --host=https://%DOMAIN% --users=30 --spawn-rate=5 --run-time=5m

REM 打開 http://localhost:8089 查看結果
```

### 步驟 8.3：性能基準測試

```cmd
REM 測試平均響應時間
ab -n 1000 -c 30 https://%DOMAIN%/health

REM 測試吞吐量
wrk -t4 -c30 -d30s https://%DOMAIN%/health
```

### 步驟 8.4：安全審計

```cmd
REM 檢查 HTTPS 配置
curl -I https://%DOMAIN%

REM 驗證 SSL 證書
openssl s_client -connect %DOMAIN%:443 -showcerts

REM 檢查 CORS 配置
curl -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -X OPTIONS https://%DOMAIN%
```

### 步驟 8.5：正式上線

```cmd
REM 最終驗證
curl https://%DOMAIN%/health
curl https://%DOMAIN%/test/json

REM 檢查日誌
gcloud logging read "resource.type=cloud_run_revision" --limit 50

REM 宣布上線
echo ✅ Anti-FraudX 已成功部署到 https://%DOMAIN%
```

---

## 📊 部署檢查清單

### 第一階段：GCP 準備
- [x] 初始化 gcloud
- [x] 設置項目
- [x] 創建服務帳戶
- [x] 授予角色
- [x] 創建密鑰
- [x] 配置 Docker
- [x] 創建 Firestore 數據庫
- [ ] 創建 Cloud Storage 存儲桶

### 第二階段：代碼遷移
- [ ] 創建 `.env.local`
- [ ] 創建 `.env.cloud`
- [ ] 驗證 Vertex AI LLM 模塊
- [ ] 驗證 LLM Factory
- [ ] 本地測試 Vertex AI 連接

### 第三階段：容器化
- [ ] 構建容器鏡像
- [ ] 推送到 Artifact Registry
- [ ] 本地測試容器

### 第四階段：後端部署
- [ ] 部署到 Cloud Run
- [ ] 配置 IAM 權限
- [ ] 測試後端 API

### 第五階段：前端部署
- [ ] 構建前端應用
- [ ] 上傳到 Cloud Storage
- [ ] 配置靜態網站託管

### 第六階段：域名配置
- [ ] 創建 DNS 區域
- [ ] 配置 DNS 記錄
- [ ] 申請 SSL 證書
- [ ] 驗證 HTTPS 連接

### 第七階段：監控設置
- [ ] 設置 Cloud Logging
- [ ] 設置 Cloud Monitoring

### 第八階段：測試上線
- [ ] 功能測試
- [ ] 負載測試
- [ ] 性能測試
- [ ] 安全審計
- [ ] 正式上線

---

## 🔑 CMD.exe 常用技巧

### 環境變量

```cmd
REM 設置環境變量
set VAR_NAME=value

REM 查看環境變量
echo %VAR_NAME%

REM 清除環境變量
set VAR_NAME=
```

### 文件操作

```cmd
REM 創建文件
(
echo 第一行
echo 第二行
) > filename.txt

REM 查看文件
type filename.txt

REM 檢查文件是否存在
if exist filename.txt (
    echo 文件存在
) else (
    echo 文件不存在
)
```

### 命令續行

```cmd
REM 使用 ^ 符號續行
docker run -it ^
  -e VAR1=value1 ^
  -e VAR2=value2 ^
  image:tag
```

### 路徑

```cmd
REM 使用正斜杠或反斜杠都可以
C:\Users\andy1\file.txt
C:/Users/andy1/file.txt

REM 進入目錄
cd backend

REM 返回上級目錄
cd ..

REM 查看當前目錄
cd
```

---

## 🚨 常見問題

### 問題 1：命令找不到
```cmd
REM 解決方案：確保 gcloud 和 docker 在 PATH 中
where gcloud
where docker
```

### 問題 2：環境變量未展開
```cmd
REM 錯誤：set VAR=%USERPROFILE%\file.txt
REM 正確：set VAR=%USERPROFILE%\file.txt
REM 然後使用：%VAR%
```

### 問題 3：路徑包含空格
```cmd
REM 使用引號
set PATH="C:\Program Files\Google\Cloud SDK"
```

---

**文檔版本**: v1.0
**最後更新**: 2026-03-15
**狀態**: 準備就緒

