# ========== 前端部署 ==========

cd "C:\Users\andy1\Desktop\新增資料夾 (2)\AI-Agent-main v9-3-11-26\AI-Agent-main
pg-platform-v2"

# 清除舊的構建
rm -r dist

# 重新構建
npm run build

# 驗證構建
ls dist/

# ========== 後端部署 ==========

cd "C:\Users\andy1\Desktop\新增資料夾 (2)\AI-Agent-main v9-3-11-26\AI-Agent-main"

# 設置環境變量
$PROJECT_ID = "anti-fraudx"
$REGION = "us-central1"
$BACKEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo/anti-fraudx-backend:latest"
$FRONTEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo/anti-fraudx-frontend:latest"

# ========== 構建並推送後端 ==========
docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .
docker push $BACKEND_IMAGE

# 部署後端到 Cloud Run
gcloud run deploy anti-fraudx-backend `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region $REGION `
  --memory 1Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.5-flash-lite,GCP_LOCATION=$REGION

# ========== 構建並推送前端 ==========

$FRONTEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/anti-fraudx-repo/anti-fraudx-frontend:latest"

docker build -t $FRONTEND_IMAGE -f Dockerfile.frontend .
docker push $FRONTEND_IMAGE
gcloud run deploy anti-fraudx-frontend --image $FRONTEND_IMAGE --platform managed --region us-central1 --allow-unauthenticated --port 8080

# ========== 驗證部署 ==========

# 獲取後端 URL
gcloud run services describe anti-fraudx-backend --region $REGION --format="value(status.url)"

# 獲取前端 URL
gcloud run services describe anti-fraudx-frontend --region $REGION --format="value(status.url)"

# 測試後端健康檢查
$BACKEND_URL = (gcloud run services describe anti-fraudx-backend --region $REGION --format="value(status.url)")
curl "$BACKEND_URL/health"

# 測試前端
$FRONTEND_URL = (gcloud run services describe anti-fraudx-frontend --region $REGION --format="value(status.url)")
Write-Host "前端 URL: $FRONTEND_URL"

-----------------------------------------------
後端
gcloud builds submit --tag us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:complete
gcloud run deploy anti-fraudx-backend --image us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:complete --region us-central1 --allow-unauthenticated --timeout 3600

前端
cd frontend
gcloud builds submit --tag us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:v1
cd ..
gcloud run deploy anti-fraudx-frontend --image us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:v1 --region us-central1 --allow-unauthenticated --port 8080

-----------------------------------------
# ========== 重啟 Backend ==========
$BACKEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:v1"

docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .
docker push $BACKEND_IMAGE
gcloud run deploy anti-fraudx-backend `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region us-central1 `
  --memory 1Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=anti-fraudx,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=us-central1

# ========== 重啟 Frontend ==========
$FRONTEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/anti-fraudx-repo/anti-fraudx-frontend:latest"

docker build -t $FRONTEND_IMAGE -f Dockerfile.frontend .
docker push $FRONTEND_IMAGE
gcloud run deploy anti-fraudx-frontend `
  --image $FRONTEND_IMAGE `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --port 8080