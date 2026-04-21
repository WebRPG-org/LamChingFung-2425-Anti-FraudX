terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.30" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.29" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

resource "terraform_data" "preflight" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      $tools = @('kubectl', 'docker', 'gcloud');
      foreach ($tool in $tools) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
          throw "Missing required tool for local-k8s: $tool"
        }
      }
      $ctx = kubectl config current-context;
      if ($ctx -ne 'docker-desktop') {
        throw "local-k8s requires docker-desktop context. Current context: $ctx"
      }
      docker version | Out-Null;
      gcloud auth list --filter=status:ACTIVE --format="value(account)" | Out-Null;
    EOT
  }
}

locals {
  namespace   = "anti-fraudx-terraform"
  alerts_path = "${path.module}/../../backend/data/scraped_alerts.json"
  rendered_resources = [
    for doc in split("\n---\n", replace(templatefile("${path.module}/resources.tftpl", {
      namespace    = local.namespace
      db_password  = var.db_password
      app_image    = var.app_image
      app_host     = var.app_host
    }), "\r\n", "\n")) : yamldecode(doc) if trimspace(doc) != ""
  ]
}

resource "google_project_service" "aiplatform" {
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false

  depends_on = [terraform_data.preflight]
}

resource "google_project_service" "iamcredentials" {
  project            = var.project_id
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "texttospeech" {
  project            = var.project_id
  service            = "texttospeech.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "vertex_runtime" {
  account_id   = var.vertex_service_account_id
  display_name = "Local Kubernetes Vertex AI runtime"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_runtime.email}"
}

resource "google_service_account_key" "vertex_runtime_key" {
  service_account_id = google_service_account.vertex_runtime.name

  depends_on = [google_project_iam_member.vertex_user]
}

resource "terraform_data" "install_local_metrics_server" {
  count = var.install_local_metrics_server ? 1 : 0

  triggers_replace = {
    kubeconfig_path = var.kubeconfig_path
    installer_rev   = "v3"
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      $ctx = kubectl config current-context;
      if ($ctx -ne 'docker-desktop') { throw "install_local_metrics_server only supports docker-desktop context. Current context: $ctx" };
      $manifest = @'
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    rbac.authorization.k8s.io/aggregate-to-admin: "true"
    rbac.authorization.k8s.io/aggregate-to-edit: "true"
    rbac.authorization.k8s.io/aggregate-to-view: "true"
    k8s-app: metrics-server
  name: system:aggregated-metrics-reader
rules:
- apiGroups:
  - metrics.k8s.io
  resources:
  - pods
  - nodes
  verbs:
  - get
  - list
  - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    k8s-app: metrics-server
  name: system:metrics-server
rules:
- apiGroups:
  - ""
  resources:
  - nodes/metrics
  verbs:
  - get
- apiGroups:
  - ""
  resources:
  - pods
  - nodes
  verbs:
  - get
  - list
  - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server-auth-reader
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: extension-apiserver-authentication-reader
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server:system:auth-delegator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    k8s-app: metrics-server
  name: system:metrics-server
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:metrics-server
subjects:
- kind: ServiceAccount
  name: metrics-server
  namespace: kube-system
---
apiVersion: v1
kind: Service
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  ports:
  - name: https
    port: 443
    protocol: TCP
    targetPort: https
  selector:
    k8s-app: metrics-server
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  strategy:
    rollingUpdate:
      maxUnavailable: 0
  template:
    metadata:
      labels:
        k8s-app: metrics-server
    spec:
      containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=10250
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
        image: registry.k8s.io/metrics-server/metrics-server:v0.8.1
        imagePullPolicy: IfNotPresent
        livenessProbe:
          failureThreshold: 3
          httpGet:
            path: /livez
            port: https
            scheme: HTTPS
          periodSeconds: 10
        name: metrics-server
        ports:
        - containerPort: 10250
          name: https
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /readyz
            port: https
            scheme: HTTPS
          initialDelaySeconds: 20
          periodSeconds: 10
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
        volumeMounts:
        - mountPath: /tmp
          name: tmp-dir
      nodeSelector:
        kubernetes.io/os: linux
      priorityClassName: system-cluster-critical
      serviceAccountName: metrics-server
      volumes:
      - emptyDir: {}
        name: tmp-dir
---
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  labels:
    k8s-app: metrics-server
  name: v1beta1.metrics.k8s.io
spec:
  group: metrics.k8s.io
  groupPriorityMinimum: 100
  insecureSkipTLSVerify: true
  service:
    name: metrics-server
    namespace: kube-system
  version: v1beta1
  versionPriority: 100
'@;
      $tmpFile = Join-Path $env:TEMP 'metrics-server-local.yaml';
      Set-Content -Path $tmpFile -Value $manifest -Encoding UTF8;
      kubectl apply -f $tmpFile;
      try {
        kubectl rollout status deployment metrics-server -n kube-system --timeout=180s;
      } catch {
        Write-Host 'metrics-server rollout failed. Dumping diagnostics...';
        kubectl get pods -n kube-system -l k8s-app=metrics-server;
        kubectl describe deployment metrics-server -n kube-system;
        kubectl describe pod -n kube-system -l k8s-app=metrics-server;
        kubectl logs -n kube-system -l k8s-app=metrics-server --all-containers=true;
        throw;
      } finally {
        Remove-Item $tmpFile -ErrorAction SilentlyContinue;
      }
    EOT
  }
}

resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = local.namespace
  }
}

resource "kubernetes_secret_v1" "app_secret" {
  metadata {
    name      = "anti-fraudx-secret"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  type = "Opaque"

  data = {
    AI_PROVIDER                    = "vertex"
    CLOUD_NAME                     = "local-k8s"
    DATABASE_URL                   = "postgresql://antifraudx:${var.db_password}@postgres.${local.namespace}.svc.cluster.local:5432/antifraudx"
    GCP_PROJECT_ID                 = var.project_id
    GCP_LOCATION                   = var.gcp_location
    VERTEX_AI_MODEL                = var.vertex_model
    GCP_LOG_NAME                   = "anti-fraudx-logs"
    GCP_MONITORING_NAMESPACE       = "anti_fraudx"
    GOOGLE_APPLICATION_CREDENTIALS = "/var/secrets/google/service-account.json"
  }
}

resource "kubernetes_secret_v1" "gcp_vertex_service_account" {
  metadata {
    name      = "gcp-vertex-service-account"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  type = "Opaque"

  data = {
    "service-account.json" = base64decode(google_service_account_key.vertex_runtime_key.private_key)
  }
}

resource "kubernetes_config_map_v1" "scraped_alerts" {
  metadata {
    name      = "scraped-alerts"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  data = {
    "scraped_alerts.json" = file(local.alerts_path)
  }
}

resource "kubernetes_manifest" "app_resources" {
  for_each = {
    for idx, manifest in nonsensitive(local.rendered_resources) : "${idx}-${manifest.kind}-${manifest.metadata.name}" => manifest
  }

  manifest = each.value

  depends_on = [
    terraform_data.install_local_metrics_server,
    kubernetes_namespace_v1.app,
    kubernetes_secret_v1.app_secret,
    kubernetes_secret_v1.gcp_vertex_service_account,
    kubernetes_config_map_v1.scraped_alerts,
  ]
}

output "vertex_runtime_service_account_email" {
  value = google_service_account.vertex_runtime.email
}

output "local_metrics_strategy" {
  value = var.install_local_metrics_server ? "Terraform triggers a local kubectl install for metrics-server on docker-desktop only; the metrics-server resources themselves are not tracked in Terraform state." : "No local metrics-server installer triggered."
}
