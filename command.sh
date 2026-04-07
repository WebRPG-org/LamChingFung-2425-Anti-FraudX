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
$BACKEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/anti-fraudx-backend:latest"
$FRONTEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/anti-fraudx-frontend:latest"

# ========== 構建並推送後端 ==========
docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .
docker push $BACKEND_IMAGE

# 部署後端到 Cloud Run
gcloud run deploy anti-fraudx-backend `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=$REGION,AUTO_LOAD_ON_STARTUP=true,FIRESTORE_PROJECT_ID=anti-fraudx,TACTIC_ANALYZER_ENABLED=true,VERDICT_JUDGE_ENABLED=true,SCAM_SCORER_ENABLED=true

# ========== 構建並推送前端 ==========

$FRONTEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:latest"

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
# ========== 重啟 Backend（混合評分系統）==========
$BACKEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-backend:hybrid-v2"

docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .
docker push $BACKEND_IMAGE

gcloud run deploy anti-fraudx-backend `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region us-central1 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=anti-fraudx,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=us-central1,AUTO_LOAD_ON_STARTUP=true,FIRESTORE_PROJECT_ID=anti-fraudx,TACTIC_ANALYZER_ENABLED=true,VERDICT_JUDGE_ENABLED=true,SCAM_SCORER_ENABLED=true,HYBRID_SCORING_ENABLED=true,ADAPTIVE_MULTIPLIER_ENABLED=true,PSYCHOLOGY_MODEL_ENABLED=true,PERFORMANCE_TRACKER_ENABLED=true

# ========== 重啟 Frontend ==========
$FRONTEND_IMAGE = "us-central1-docker.pkg.dev/anti-fraudx/cloud-run-source-deploy/anti-fraudx-frontend:latest"

docker build -t $FRONTEND_IMAGE -f Dockerfile.frontend .
docker push $FRONTEND_IMAGE
gcloud run deploy anti-fraudx-frontend `
  --image $FRONTEND_IMAGE `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --port 8080

# ========== ONE-CLICK BACKEND DEPLOYER ==========
$ErrorActionPreference = "Stop"

$PROJECT_ID = "anti-fraudx"
$REGION = "us-central1"
$SERVICE_NAME = "anti-fraudx-backend"
$BACKEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/${SERVICE_NAME}:hybrid-v1"

Write-Host "[1/3] Building image: $BACKEND_IMAGE"
docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .

Write-Host "[2/3] Pushing image"
docker push $BACKEND_IMAGE

Write-Host "[3/3] Deploying to Cloud Run"
gcloud run deploy $SERVICE_NAME `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=$REGION,AUTO_LOAD_ON_STARTUP=true,FIRESTORE_PROJECT_ID=$PROJECT_ID,TACTIC_ANALYZER_ENABLED=true,VERDICT_JUDGE_ENABLED=true,SCAM_SCORER_ENABLED=true,HYBRID_SCORING_ENABLED=true,ADAPTIVE_MULTIPLIER_ENABLED=true,PSYCHOLOGY_MODEL_ENABLED=true,PERFORMANCE_TRACKER_ENABLED=true

$BACKEND_URL = (gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
Write-Host "✅ Deploy complete: $BACKEND_URL"
Write-Host "✅ Health check: $BACKEND_URL/health"

# =====================================================================
# ========== 多語言 + 粵語 TTS 完整部署（計劃書版本）==========
# 包含：多語言UI/對話/STT/TTS、粵語語音包、前端全面本地化
# 執行方法：複製以下整段到 PowerShell 執行
# =====================================================================
$ErrorActionPreference = "Stop"

$PROJECT_ID   = "anti-fraudx"
$REGION       = "us-central1"
$SERVICE_NAME = "anti-fraudx-backend"
$BACKEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/${SERVICE_NAME}:3platform-tts-v4"

# ── Step 1: 前端 Build（包含多語言 + i18n 修復）──
Write-Host "[1/5] Building frontend..."
Set-Location "c:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-3-16-26\AI-Agent-main\rpg-platform-v2"
npm run build
Write-Host "✅ Frontend build complete"

# ── Step 2: 後端 Docker Build ──
Write-Host "[2/5] Building backend image: $BACKEND_IMAGE"
Set-Location "c:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-3-16-26\AI-Agent-main"
docker build -t $BACKEND_IMAGE -f Dockerfile.cloud .

# ── Step 3: Push 到 Artifact Registry ──
Write-Host "[3/5] Pushing image..."
docker push $BACKEND_IMAGE

# ── Step 4: 部署後端（含 TTS 粵語聲音包 env vars）──
Write-Host "[4/5] Deploying backend to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.5-flash,GCP_LOCATION=$REGION,AUTO_LOAD_ON_STARTUP=true,FIRESTORE_PROJECT_ID=$PROJECT_ID,TACTIC_ANALYZER_ENABLED=true,VERDICT_JUDGE_ENABLED=true,SCAM_SCORER_ENABLED=true,HYBRID_SCORING_ENABLED=true,ADAPTIVE_MULTIPLIER_ENABLED=true,PSYCHOLOGY_MODEL_ENABLED=true,PERFORMANCE_TRACKER_ENABLED=true,TTS_VOICE_SCAMMER=yue-HK-Standard-B,TTS_VOICE_VICTIM=yue-HK-Standard-C,TTS_VOICE_EXPERT=yue-HK-Standard-A

# ── Step 5: 部署完成（權限已在首次設定，無需每次執行）──
Write-Host "[5/5] Skipping IAM step (one-time only, already set)."
Write-Host "      如需重新授權，請單獨執行下方 [首次授權] 段落。"

# ── 驗證 ──
$BACKEND_URL = (gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
Write-Host ""
Write-Host "✅ 部署完成！"
Write-Host "   Backend URL  : $BACKEND_URL"
Write-Host "   Health check : $BACKEND_URL/health"
Write-Host "   TTS 粵語測試 : $BACKEND_URL/api/tts/test?role=scammer&language=zh-HK"
Write-Host "   TTS 聲音列表 : $BACKEND_URL/api/tts/voices?language=yue-HK"
Write-Host ""
Write-Host "如瀏覽器聽到粵語語音 = 部署成功"
Write-Host "如返回 403    = 請執行下方 [首次授權] 段落"
Write-Host "如返回 500    = 請查 Cloud Run 日誌排查後端錯誤"

# =====================================================================
# ========== [首次授權] Cloud TTS IAM 權限 ==========
# 只需執行一次，之後每次重啟/重新部署都唔需要再執行
# 如收到 403 TTS 錯誤，先執行呢段
# =====================================================================
$PROJECT_ID   = "anti-fraudx"
$REGION       = "us-central1"
$SERVICE_NAME = "anti-fraudx-backend"

$SA = (gcloud run services describe $SERVICE_NAME --region $REGION --format="value(spec.template.spec.serviceAccountName)")
if ($SA) {
  gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA" `
    --role="roles/cloudtts.client"
  Write-Host "✅ TTS permission granted to: $SA"
  Write-Host "   之後重啟唔需要再執行呢段"
} else {
  Write-Host "⚠️  無法自動偵測 SA，請手動執行："
  Write-Host "   gcloud projects add-iam-policy-binding $PROJECT_ID --member='serviceAccount:YOUR_SA@anti-fraudx.iam.gserviceaccount.com' --role='roles/cloudtts.client'"
}
