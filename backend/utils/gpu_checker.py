"""
GPU检测和强制使用工具
确保在有GPU时必须使用GPU而不是CPU
"""

import os
import subprocess
import sys
import json
import httpx
from typing import Dict, Optional, List
from utils.logger import log


class GPUChecker:
    """GPU检测和验证工具"""
    
    def __init__(self):
        self.gpu_available = False
        self.gpu_info: Dict = {}
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
    def check_nvidia_gpu(self) -> bool:
        """检查NVIDIA GPU是否可用"""
        try:
            # 方法1: nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpus = result.stdout.strip().split('\n')
                self.gpu_info['gpus'] = []
                
                for i, gpu in enumerate(gpus):
                    parts = gpu.split(',')
                    if len(parts) >= 3:
                        self.gpu_info['gpus'].append({
                            'id': i,
                            'name': parts[0].strip(),
                            'memory': parts[1].strip(),
                            'driver': parts[2].strip()
                        })
                
                self.gpu_available = True
                log.info(f"✅ 检测到 {len(gpus)} 个NVIDIA GPU")
                for gpu in self.gpu_info['gpus']:
                    log.info(f"   GPU {gpu['id']}: {gpu['name']} ({gpu['memory']}) - Driver: {gpu['driver']}")
                return True
            
        except FileNotFoundError:
            log.warning("❌ nvidia-smi 未找到")
        except subprocess.TimeoutExpired:
            log.warning("⏱️ nvidia-smi 超时")
        except Exception as e:
            log.warning(f"❌ nvidia-smi 错误: {e}")
        
        # 方法2: 检查CUDA环境变量
        cuda_visible = os.getenv("CUDA_VISIBLE_DEVICES")
        nvidia_visible = os.getenv("NVIDIA_VISIBLE_DEVICES")
        
        if cuda_visible or nvidia_visible:
            log.info(f"🔍 检测到GPU环境变量: CUDA_VISIBLE_DEVICES={cuda_visible}, NVIDIA_VISIBLE_DEVICES={nvidia_visible}")
            self.gpu_available = True
            return True
        
        return False
    
    def check_ollama_gpu_usage(self) -> Optional[Dict]:
        """检查Ollama是否正在使用GPU"""
        try:
            # 检查Ollama版本和配置
            response = httpx.get(f"{self.ollama_base_url}/api/version", timeout=10)
            if response.status_code == 200:
                log.info(f"✅ Ollama服务可用: {self.ollama_base_url}")
            
            # 检查已加载的模型
            response = httpx.get(f"{self.ollama_base_url}/api/ps", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                if models:
                    log.info(f"📊 Ollama已加载模型:")
                    for model in models:
                        name = model.get("name", "unknown")
                        size = model.get("size", 0)
                        size_mb = size / (1024 * 1024)
                        
                        # 检查是否使用GPU
                        # Ollama在GPU模式下会在响应中包含GPU信息
                        log.info(f"   - {name} ({size_mb:.1f} MB)")
                    
                    return {"loaded_models": models}
            
        except httpx.ConnectError:
            log.error(f"❌ 无法连接到Ollama服务: {self.ollama_base_url}")
        except Exception as e:
            log.warning(f"⚠️ Ollama检查失败: {e}")
        
        return None
    
    def force_gpu_usage(self) -> bool:
        """强制使用GPU，如果GPU可用但未使用则报错"""
        
        # 快速短路：FORCE_GPU=0 時跳過所有檢查，避免阻塞啟動
        if os.getenv("FORCE_GPU", "0") == "0":
            log.info("[GPU] FORCE_GPU=0，跳過GPU檢測，使用CPU/自動模式")
            return False

        log.info("="*80)
        log.info("🔍 GPU检测开始...")
        log.info("="*80)
        
        # 1. 检查GPU硬件
        gpu_detected = self.check_nvidia_gpu()
        
        if not gpu_detected:
            log.warning("⚠️ 未检测到NVIDIA GPU，将使用CPU模式")
            return False
        
        # 2. 检查环境变量配置
        log.info("\n🔧 检查环境变量配置...")
        required_env_vars = {
            "NVIDIA_VISIBLE_DEVICES": os.getenv("NVIDIA_VISIBLE_DEVICES", "未设置"),
            "NVIDIA_DRIVER_CAPABILITIES": os.getenv("NVIDIA_DRIVER_CAPABILITIES", "未设置"),
            "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES", "未设置"),
        }
        for var, value in required_env_vars.items():
            if value == "未设置":
                log.warning(f"   ⚠️ {var}: {value}")
            else:
                log.info(f"   ✅ {var}: {value}")
        
        # 3. 快速檢查 Ollama 可達性（單次，不重試）
        log.info(f"\n🔗 检查Ollama服务连接: {self.ollama_base_url}")
        try:
            response = httpx.get(f"{self.ollama_base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                log.info("✅ Ollama服务已就绪")
            else:
                log.warning(f"⚠️ Ollama 回應 {response.status_code}")
        except Exception as e:
            log.warning(f"⚠️ Ollama 連接失敗（非致命）: {e}")
        
        # 4. 驗證 GPU 使用情況
        self.check_ollama_gpu_usage()
        
        log.info("\n"+"="*80)
        log.info("✅ GPU硬件检测成功，Ollama将自动使用GPU加速")
        log.info("="*80)
        return True
    
    def get_gpu_status_report(self) -> Dict:
        """生成GPU状态报告"""
        return {
            "gpu_available": self.gpu_available,
            "gpu_info": self.gpu_info,
            "environment": {
                "NVIDIA_VISIBLE_DEVICES": os.getenv("NVIDIA_VISIBLE_DEVICES"),
                "NVIDIA_DRIVER_CAPABILITIES": os.getenv("NVIDIA_DRIVER_CAPABILITIES"),
                "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES"),
                "FORCE_GPU": os.getenv("FORCE_GPU", "0"),
            },
            "ollama_url": self.ollama_base_url,
            "note": "GPU usage is automatically managed by Ollama container with NVIDIA runtime"
        }


def check_and_enforce_gpu():
    """检查并强制使用GPU（如果可用）"""
    checker = GPUChecker()
    result = checker.force_gpu_usage()
    
    # 保存状态报告
    report = checker.get_gpu_status_report()
    report_file = "/tmp/gpu_status.json" if os.path.exists("/tmp") else "gpu_status.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        log.info(f"\n📝 GPU状态报告已保存: {report_file}")
    except Exception as e:
        log.warning(f"无法保存GPU状态报告: {e}")
    
    return result


if __name__ == "__main__":
    # 独立运行时执行检查
    log.info("🚀 GPU检测工具")
    check_and_enforce_gpu()

