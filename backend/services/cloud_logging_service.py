"""
Cloud Logging Service - 多雲原生日誌集成
支持 Anti-FraudX 在 GCP / AWS / Azure 上的日誌管理
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
import requests
from google.cloud import logging as cloud_logging
from utils.logger import log


class CloudLoggingService:
    """
    Cloud Logging 服務類
    根據 CLOUD_NAME 自動選擇 GCP / AWS / Azure 原生日誌後端。
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CloudLoggingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_name: str = "anti-fraudx-logs"):
        if CloudLoggingService._initialized:
            return

        self.log_name = log_name
        self.cloud_name = os.getenv("CLOUD_NAME", "gcp").strip().lower()
        self.hostname = socket.gethostname()
        self.backend = "local"
        self._gcp_client = None
        self._gcp_logger = None
        self._aws_client = None
        self._aws_log_group = os.getenv("AWS_LOG_GROUP_NAME", f"/anti-fraudx/{self.log_name}")
        self._aws_log_stream = os.getenv(
            "AWS_LOG_STREAM_NAME",
            f"{self.hostname}-{os.getpid()}"
        )
        self._aws_sequence_token = None
        self._azure_workspace_id = os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID", "")
        self._azure_shared_key = os.getenv("AZURE_LOG_ANALYTICS_SHARED_KEY", "")
        self._azure_log_type = os.getenv("AZURE_LOG_TYPE", "AntiFraudXLogs")

        try:
            if self.cloud_name in {"gcp", "gke", "local-k8s"}:
                self._init_gcp()
            elif self.cloud_name == "aws":
                self._init_aws()
            elif self.cloud_name == "azure":
                self._init_azure()
            else:
                log.warning(
                    f"[CLOUD_LOGGING_SERVICE] ⚠️ 未知 CLOUD_NAME={self.cloud_name}，改用本地 logging fallback"
                )
                self.backend = "local"

            CloudLoggingService._initialized = True
        except Exception as e:
            self.backend = "local"
            CloudLoggingService._initialized = True
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 初始化失敗，改用本地 fallback: {str(e)}")

    def _init_gcp(self) -> None:
        self._gcp_client = cloud_logging.Client()
        self._gcp_logger = self._gcp_client.logger(self.log_name)

        root_logger = logging.getLogger()
        has_handler = any(
            handler.__class__.__name__ == "CloudLoggingHandler"
            for handler in root_logger.handlers
        )
        if not has_handler:
            cloud_handler = cloud_logging.handlers.CloudLoggingHandler(
                self._gcp_client,
                name=self.log_name,
            )
            root_logger.addHandler(cloud_handler)

        self.backend = "gcp"
        log.info(f"[CLOUD_LOGGING_SERVICE] ✅ GCP Cloud Logging 已啟用 - log_name={self.log_name}")

    def _init_aws(self) -> None:
        region_name = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-east-1"))
        self._aws_client = boto3.client("logs", region_name=region_name)

        try:
            self._aws_client.create_log_group(logGroupName=self._aws_log_group)
        except self._aws_client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            self._aws_client.create_log_stream(
                logGroupName=self._aws_log_group,
                logStreamName=self._aws_log_stream,
            )
        except self._aws_client.exceptions.ResourceAlreadyExistsException:
            pass

        self._aws_sequence_token = self._get_aws_sequence_token()
        self.backend = "aws"
        log.info(
            "[CLOUD_LOGGING_SERVICE] ✅ AWS CloudWatch Logs 已啟用 - "
            f"group={self._aws_log_group}, stream={self._aws_log_stream}"
        )

    def _init_azure(self) -> None:
        if not self._azure_workspace_id or not self._azure_shared_key:
            raise ValueError(
                "Azure logging requires AZURE_LOG_ANALYTICS_WORKSPACE_ID and AZURE_LOG_ANALYTICS_SHARED_KEY"
            )

        self.backend = "azure"
        log.info(
            "[CLOUD_LOGGING_SERVICE] ✅ Azure Log Analytics 已啟用 - "
            f"log_type={self._azure_log_type}"
        )

    def _serialize_payload(
        self,
        severity: str,
        message: str,
        labels: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "message": message,
            "severity": severity,
            "cloud_name": self.cloud_name,
            "hostname": self.hostname,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if labels:
            payload["labels"] = labels
        if extra:
            payload.update(extra)
        return payload

    def _emit(self, severity: str, message: str, labels: Optional[Dict[str, str]] = None, extra: Optional[Dict[str, Any]] = None) -> None:
        payload = self._serialize_payload(severity=severity, message=message, labels=labels, extra=extra)

        try:
            if self.backend == "gcp" and self._gcp_logger is not None:
                self._gcp_logger.log_struct(payload, labels=labels or {})
                return

            if self.backend == "aws" and self._aws_client is not None:
                self._emit_aws(payload)
                return

            if self.backend == "azure":
                self._emit_azure(payload)
                return
        except Exception as e:
            log.error(f"[CLOUD_LOGGING_SERVICE] ❌ 原生日誌寫入失敗，改寫本地 logger: {str(e)}")

        self._emit_local(severity, payload)

    def _emit_local(self, severity: str, payload: Dict[str, Any]) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        level = severity.upper()
        if level == "ERROR":
            log.error(line)
        elif level == "WARNING":
            log.warning(line)
        elif level == "DEBUG":
            log.debug(line)
        else:
            log.info(line)

    def _get_aws_sequence_token(self) -> Optional[str]:
        response = self._aws_client.describe_log_streams(
            logGroupName=self._aws_log_group,
            logStreamNamePrefix=self._aws_log_stream,
        )
        for stream in response.get("logStreams", []):
            if stream.get("logStreamName") == self._aws_log_stream:
                return stream.get("uploadSequenceToken")
        return None

    def _emit_aws(self, payload: Dict[str, Any]) -> None:
        event = {
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "message": json.dumps(payload, ensure_ascii=False),
        }
        kwargs: Dict[str, Any] = {
            "logGroupName": self._aws_log_group,
            "logStreamName": self._aws_log_stream,
            "logEvents": [event],
        }
        if self._aws_sequence_token:
            kwargs["sequenceToken"] = self._aws_sequence_token

        try:
            response = self._aws_client.put_log_events(**kwargs)
            self._aws_sequence_token = response.get("nextSequenceToken")
        except self._aws_client.exceptions.InvalidSequenceTokenException:
            self._aws_sequence_token = self._get_aws_sequence_token()
            if self._aws_sequence_token:
                kwargs["sequenceToken"] = self._aws_sequence_token
            else:
                kwargs.pop("sequenceToken", None)
            response = self._aws_client.put_log_events(**kwargs)
            self._aws_sequence_token = response.get("nextSequenceToken")

    def _build_azure_signature(self, date_string: str, content_length: int, method: str, content_type: str, resource: str) -> str:
        x_headers = f"x-ms-date:{date_string}"
        string_to_hash = f"{method}\n{content_length}\n{content_type}\n{x_headers}\n{resource}"
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self._azure_shared_key)
        encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
        return f"SharedKey {self._azure_workspace_id}:{encoded_hash}"

    def _emit_azure(self, payload: Dict[str, Any]) -> None:
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

    def log_info(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        self._emit("INFO", message, labels=labels)

    def log_warning(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        self._emit("WARNING", message, labels=labels)

    def log_error(self, message: str, error: Optional[Exception] = None, labels: Optional[Dict[str, str]] = None) -> None:
        self._emit(
            "ERROR",
            message,
            labels=labels,
            extra={"error": str(error) if error else ""},
        )

    def log_debug(self, message: str, labels: Optional[Dict[str, str]] = None) -> None:
        self._emit("DEBUG", message, labels=labels)

    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        self._emit(
            "INFO",
            f"event:{event_type}",
            labels=labels,
            extra={
                "event_type": event_type,
                "event_data": event_data,
            },
        )

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        status: str = "success",
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        self._emit(
            "INFO",
            f"performance:{operation}",
            labels=labels,
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "status": status,
            },
        )

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        self._emit(
            "INFO",
            f"api:{method} {path}",
            labels=labels,
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    def get_logger(self):
        if self.backend == "gcp":
            return self._gcp_logger
        if self.backend == "aws":
            return self._aws_client
        if self.backend == "azure":
            return {
                "workspace_id": self._azure_workspace_id,
                "log_type": self._azure_log_type,
            }
        return log
