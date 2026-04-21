"""
Cloud Monitoring Service - 多雲原生監控集成
支持 Anti-FraudX 在 GCP / AWS / Azure 上的監控和指標
"""

import base64
import hashlib
import hmac
import json
import os
import socket
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
import requests
from google.cloud import monitoring_v3
from utils.logger import log


class CloudMonitoringService:
    """
    Cloud Monitoring 服務類
    根據 CLOUD_NAME 自動選擇 GCP / AWS / Azure 原生監控後端。
    保持既有調用接口不變。
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CloudMonitoringService, cls).__new__(cls)
        return cls._instance

    def __init__(self, project_id: Optional[str] = None):
        if CloudMonitoringService._initialized:
            return

        self.cloud_name = os.getenv("CLOUD_NAME", "gcp").strip().lower()
        self.hostname = socket.gethostname()
        self.backend = "local"

        self._gcp_project_id = project_id or os.getenv("GCP_PROJECT_ID", "anti-fraudx-us-ci")
        self._gcp_client = None

        self._aws_region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-east-1"))
        self._aws_namespace = os.getenv("AWS_MONITORING_NAMESPACE", "AntiFraudX")
        self._aws_client = None

        self._azure_workspace_id = os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID", "")
        self._azure_shared_key = os.getenv("AZURE_LOG_ANALYTICS_SHARED_KEY", "")
        self._azure_log_type = os.getenv("AZURE_MONITOR_LOG_TYPE", "AntiFraudXMetrics")

        try:
            if self.cloud_name in {"gcp", "gke", "local-k8s"}:
                self._init_gcp()
            elif self.cloud_name == "aws":
                self._init_aws()
            elif self.cloud_name == "azure":
                self._init_azure()
            else:
                log.warning(
                    f"[CLOUD_MONITORING_SERVICE] ⚠️ 未知 CLOUD_NAME={self.cloud_name}，改用本地 fallback"
                )
                self.backend = "local"

            CloudMonitoringService._initialized = True
        except Exception as e:
            self.backend = "local"
            CloudMonitoringService._initialized = True
            log.error(f"[CLOUD_MONITORING_SERVICE] ❌ 初始化失敗，改用本地 fallback: {str(e)}")

    def _init_gcp(self) -> None:
        self._gcp_client = monitoring_v3.MetricServiceClient()
        self.backend = "gcp"
        log.info(
            f"[CLOUD_MONITORING_SERVICE] ✅ GCP Cloud Monitoring 已啟用 - 項目: {self._gcp_project_id}"
        )

    def _init_aws(self) -> None:
        self._aws_client = boto3.client("cloudwatch", region_name=self._aws_region)
        self.backend = "aws"
        log.info(
            "[CLOUD_MONITORING_SERVICE] ✅ AWS CloudWatch Metrics 已啟用 - "
            f"namespace: {self._aws_namespace}, region: {self._aws_region}"
        )

    def _init_azure(self) -> None:
        if not self._azure_workspace_id or not self._azure_shared_key:
            raise ValueError(
                "Azure monitoring requires AZURE_LOG_ANALYTICS_WORKSPACE_ID and AZURE_LOG_ANALYTICS_SHARED_KEY"
            )
        self.backend = "azure"
        log.info(
            "[CLOUD_MONITORING_SERVICE] ✅ Azure Monitor(Log Analytics fallback) 已啟用 - "
            f"log_type: {self._azure_log_type}"
        )

    def _normalize_metric_name(self, metric_type: str) -> str:
        name = metric_type.split("/")[-1]
        return name.replace("-", "_")

    def _build_payload(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        resource_type: str = "global",
    ) -> Dict[str, Any]:
        return {
            "metric_type": metric_type,
            "metric_name": self._normalize_metric_name(metric_type),
            "value": value,
            "labels": labels or {},
            "resource_type": resource_type,
            "cloud_name": self.cloud_name,
            "hostname": self.hostname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        resource_type: str = "global"
    ) -> bool:
        payload = self._build_payload(
            metric_type=metric_type,
            value=value,
            labels=labels,
            resource_type=resource_type,
        )

        try:
            if self.backend == "gcp":
                self._write_metric_gcp(payload)
            elif self.backend == "aws":
                self._write_metric_aws(payload)
            elif self.backend == "azure":
                self._write_metric_azure(payload)
            else:
                self._write_metric_local(payload)

            log.info(
                f"[CLOUD_MONITORING_SERVICE] ✅ 指標已寫入 - 類型: {metric_type}, 值: {value}, backend: {self.backend}"
            )
            return True
        except Exception as e:
            log.error(f"[CLOUD_MONITORING_SERVICE] ❌ 寫入指標失敗: {str(e)}")
            self._write_metric_local(payload)
            return False

    def _write_metric_gcp(self, payload: Dict[str, Any]) -> None:
        project_name = f"projects/{self._gcp_project_id}"
        series = monitoring_v3.TimeSeries()
        series.metric.type = payload["metric_type"]

        for key, value_str in payload["labels"].items():
            series.metric.labels[key] = str(value_str)

        series.resource.type = payload["resource_type"]
        point = monitoring_v3.Point()
        interval = monitoring_v3.TimeInterval()
        now = datetime.now(timezone.utc)
        seconds = int(now.timestamp())
        nanos = int((now.timestamp() - seconds) * 1_000_000_000)
        interval.end_time.seconds = seconds
        interval.end_time.nanos = nanos
        point.interval = interval
        point.value.double_value = float(payload["value"])
        series.points = [point]

        self._gcp_client.create_time_series(name=project_name, time_series=[series])

    def _write_metric_aws(self, payload: Dict[str, Any]) -> None:
        dimensions = [
            {"Name": str(key)[:255], "Value": str(value)[:255]}
            for key, value in payload["labels"].items()
        ]
        dimensions.append({"Name": "Hostname", "Value": self.hostname[:255]})

        self._aws_client.put_metric_data(
            Namespace=self._aws_namespace,
            MetricData=[
                {
                    "MetricName": payload["metric_name"][:255],
                    "Timestamp": datetime.now(timezone.utc),
                    "Value": float(payload["value"]),
                    "Unit": "None",
                    "Dimensions": dimensions,
                }
            ],
        )

    def _build_azure_signature(self, date_string: str, content_length: int, method: str, content_type: str, resource: str) -> str:
        x_headers = f"x-ms-date:{date_string}"
        string_to_hash = f"{method}\n{content_length}\n{content_type}\n{x_headers}\n{resource}"
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self._azure_shared_key)
        encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
        return f"SharedKey {self._azure_workspace_id}:{encoded_hash}"

    def _write_metric_azure(self, payload: Dict[str, Any]) -> None:
        body = json.dumps([payload], ensure_ascii=False)
        body_bytes = body.encode("utf-8")
        method = "POST"
        content_type = "application/json"
        resource = "/api/logs"
        rfc1123date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature = self._build_azure_signature(
            date_string=rfc1123date,
            content_length=len(body_bytes),
            method=method,
            content_type=content_type,
            resource=resource,
        )

        uri = (
            f"https://{self._azure_workspace_id}.ods.opinsights.azure.com"
            f"{resource}?api-version=2016-04-01"
        )
        headers = {
            "Content-Type": content_type,
            "Authorization": signature,
            "Log-Type": self._azure_log_type,
            "x-ms-date": rfc1123date,
            "time-generated-field": "timestamp",
        }
        response = requests.post(uri, data=body_bytes, headers=headers, timeout=10)
        response.raise_for_status()

    def _write_metric_local(self, payload: Dict[str, Any]) -> None:
        log.info(
            f"[CLOUD_MONITORING_SERVICE][LOCAL_FALLBACK] {json.dumps(payload, ensure_ascii=False)}"
        )

    def record_api_latency(self, endpoint: str, latency_ms: float) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/api_latency",
            value=latency_ms,
            labels={"endpoint": endpoint}
        )

    def record_error_count(self, error_type: str, count: int = 1) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/error_count",
            value=float(count),
            labels={"error_type": error_type}
        )

    def record_game_session_count(self, count: int) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/game_session_count",
            value=float(count)
        )

    def record_active_users(self, count: int) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/active_users",
            value=float(count)
        )

    def record_model_inference_time(self, model_name: str, inference_time_ms: float) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/model_inference_time",
            value=inference_time_ms,
            labels={"model": model_name}
        )

    def record_token_usage(self, model: str, tokens: int) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/token_usage",
            value=float(tokens),
            labels={"model": model}
        )

    def record_database_operation(self, operation: str, duration_ms: float) -> bool:
        return self.write_metric(
            metric_type="custom.googleapis.com/anti_fraudx/database_operation_time",
            value=duration_ms,
            labels={"operation": operation}
        )

    def get_client(self):
        if self.backend == "gcp":
            return self._gcp_client
        if self.backend == "aws":
            return self._aws_client
        if self.backend == "azure":
            return {
                "workspace_id": self._azure_workspace_id,
                "log_type": self._azure_log_type,
            }
        return None
