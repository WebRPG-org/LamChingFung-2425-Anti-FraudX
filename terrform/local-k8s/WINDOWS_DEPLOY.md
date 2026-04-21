# Windows 本地部署（Docker Desktop Kubernetes）

## 1. 確保 context 正確
```powershell
kubectl config use-context docker-desktop
kubectl get nodes
```

## 2. 去專案根目錄 build image
```powershell
cd "C:\Users\andy1\Desktop\3-16-26-ANTI-FRAUDX\AI-Agent-main v9-4-7-26\AI-Agent-main"
docker build -t anti-fraudx:latest .
```

## 3. 部署 local-k8s
```powershell
cd ".\terrform\local-k8s"
kubectl create namespace anti-fraudx --dry-run=client -o yaml | kubectl apply -f -
kubectl delete configmap scraped-alerts -n anti-fraudx --ignore-not-found
kubectl create configmap scraped-alerts --from-file=scraped_alerts.json=..\..\backend\data\scraped_alerts.json -n anti-fraudx
kubectl apply -f .\app-manifests.yaml
```

## 4. 檢查
```powershell
kubectl get all -n anti-fraudx
kubectl get ingress -n anti-fraudx
kubectl get pvc -n anti-fraudx
```

## 5. 如 pod 出錯
```powershell
kubectl get pods -n anti-fraudx
kubectl logs -n anti-fraudx deployment/anti-fraudx
kubectl logs -n anti-fraudx postgres-0
```

## 6. 可選：本地 host 映射
將以下加入 `hosts`：
```text
127.0.0.1 anti-fraudx.local
```

## 備註
- 此版本已改成使用本地 image `anti-fraudx:latest`
- 本地 ingress 先不強制 TLS，減少啟動失敗機會
- PostgreSQL 預設密碼：`240302611`
