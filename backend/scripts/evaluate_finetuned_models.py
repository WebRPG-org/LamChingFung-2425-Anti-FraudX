"""
Fine-Tuned模型評估工具
用於評估和對比專家/騙徒模型的性能

使用方法：
1. 評估專家模型：python backend/scripts/evaluate_finetuned_models.py --model expert --model-name anti-fraud-expert-20241111
2. 對比兩個模型：python backend/scripts/evaluate_finetuned_models.py --compare model1 model2
3. 批量評估：python backend/scripts/evaluate_finetuned_models.py --batch
"""

import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import asyncio

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log
from llms.ollama_llm import OllamaLlm


class ModelEvaluator:
    """模型評估器"""
    
    def __init__(self):
        self.test_cases_dir = Path("backend/test_cases")
        self.test_cases_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir = Path("backend/evaluation_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_test_cases(self, model_type: str) -> List[Dict[str, Any]]:
        """
        加載測試用例
        
        Args:
            model_type: "expert" or "scammer"
        
        Returns:
            測試用例列表
        """
        test_file = self.test_cases_dir / f"{model_type}_test_cases.json"
        
        if not test_file.exists():
            log.warning(f"測試用例文件不存在: {test_file}")
            # 創建默認測試用例
            self._create_default_test_cases(model_type, test_file)
        
        with open(test_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        
        log.info(f"加載 {len(test_cases)} 個 {model_type} 測試用例")
        return test_cases
    
    def _create_default_test_cases(self, model_type: str, output_file: Path):
        """創建默認測試用例"""
        if model_type == "expert":
            test_cases = [
                {
                    "id": "expert_001",
                    "scenario": "電話詐騙-假冒警察",
                    "context": "受騙者：喂？\n騙徒：你好，我係警察李sir，你嘅銀行帳戶涉嫌洗黑錢，請立即配合調查。",
                    "expected_keywords": ["唔使驚", "騙局", "掛線", "核實"],
                    "difficulty": "medium"
                },
                {
                    "id": "expert_002",
                    "scenario": "投資詐騙-高回報誘惑",
                    "context": "受騙者：咩投資咁好？\n騙徒：我哋嘅投資計劃保證月回報20%，絕對安全，今日最後一日優惠。",
                    "expected_keywords": ["唔合理", "風險", "詐騙", "證監會"],
                    "difficulty": "easy"
                },
                {
                    "id": "expert_003",
                    "scenario": "複雜詐騙-多重權威",
                    "context": "受騙者：我應該點做？\n騙徒：我係警察，你現在必須配合。\n受騙者：但係...\n騙徒：唔配合就會被拘捕，你想坐監？",
                    "expected_keywords": ["冷靜", "核實", "打去警署", "假冒"],
                    "difficulty": "hard"
                }
            ]
        else:  # scammer
            test_cases = [
                {
                    "id": "scammer_001",
                    "scenario": "初次接觸-建立權威",
                    "context": "受騙者：你係邊個？",
                    "expected_keywords": ["警察", "銀行", "緊急", "重要"],
                    "difficulty": "easy"
                },
                {
                    "id": "scammer_002",
                    "scenario": "應對質疑-升級壓力",
                    "context": "受騙者：點解我要信你？\n專家：佢可能係騙徒，唔好信佢。",
                    "expected_keywords": ["證據", "權威", "法律", "後果"],
                    "difficulty": "hard"
                }
            ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)
        
        log.info(f"創建默認測試用例: {output_file}")
    
    async def evaluate_single_response(
        self,
        model_name: str,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        評估單個回應
        
        Args:
            model_name: 模型名稱
            test_case: 測試用例
        
        Returns:
            評估結果
        """
        try:
            # 創建LLM實例
            llm = OllamaLlm(model_name=model_name)
            
            # 構建提示
            context = test_case.get("context", "")
            prompt = f"【情境】{test_case.get('scenario', '')}\n\n【對話記錄】\n{context}\n\n【你的任務】請給出你的回應："
            
            # 生成回應
            response = await llm.generate(prompt)
            
            # 評估回應
            expected_keywords = test_case.get("expected_keywords", [])
            found_keywords = [kw for kw in expected_keywords if kw in response]
            
            keyword_score = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
            
            # 長度評分
            length = len(response)
            if 50 <= length <= 300:
                length_score = 1.0
            elif length < 50:
                length_score = 0.5
            else:
                length_score = 0.8
            
            # 總分
            total_score = (keyword_score * 0.7 + length_score * 0.3) * 100
            
            result = {
                "test_case_id": test_case.get("id"),
                "scenario": test_case.get("scenario"),
                "difficulty": test_case.get("difficulty"),
                "response": response,
                "response_length": length,
                "expected_keywords": expected_keywords,
                "found_keywords": found_keywords,
                "keyword_score": keyword_score,
                "length_score": length_score,
                "total_score": total_score,
                "passed": total_score >= 60
            }
            
            return result
            
        except Exception as e:
            log.error(f"評估失敗 (test_case={test_case.get('id')}): {e}")
            return {
                "test_case_id": test_case.get("id"),
                "error": str(e),
                "passed": False,
                "total_score": 0
            }
    
    async def evaluate_model(
        self,
        model_name: str,
        model_type: str
    ) -> Dict[str, Any]:
        """
        評估整個模型
        
        Args:
            model_name: 模型名稱
            model_type: "expert" or "scammer"
        
        Returns:
            完整評估結果
        """
        log.info(f"{'='*60}")
        log.info(f"開始評估模型: {model_name} (type={model_type})")
        log.info(f"{'='*60}")
        
        # 加載測試用例
        test_cases = self.load_test_cases(model_type)
        
        # 評估每個測試用例
        results = []
        for i, test_case in enumerate(test_cases, 1):
            log.info(f"測試 {i}/{len(test_cases)}: {test_case.get('id')}")
            result = await self.evaluate_single_response(model_name, test_case)
            results.append(result)
            
            if result.get("passed"):
                log.info(f"  ✅ 通過 (分數: {result.get('total_score', 0):.1f})")
            else:
                log.warning(f"  ❌ 失敗 (分數: {result.get('total_score', 0):.1f})")
        
        # 計算總體統計
        total_score = sum(r.get("total_score", 0) for r in results) / len(results) if results else 0
        pass_rate = sum(1 for r in results if r.get("passed", False)) / len(results) if results else 0
        
        evaluation_result = {
            "model_name": model_name,
            "model_type": model_type,
            "timestamp": datetime.now().isoformat(),
            "total_score": total_score,
            "pass_rate": pass_rate,
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "passed_tests": sum(1 for r in results if r.get("passed", False)),
                "failed_tests": sum(1 for r in results if not r.get("passed", False)),
                "average_score": total_score
            }
        }
        
        # 保存評估結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"eval_{model_type}_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
        
        log.info(f"\n{'='*60}")
        log.info(f"📊 評估結果總結")
        log.info(f"{'='*60}")
        log.info(f"模型: {model_name}")
        log.info(f"總分: {total_score:.1f}/100")
        log.info(f"通過率: {pass_rate*100:.1f}%")
        log.info(f"通過: {evaluation_result['summary']['passed_tests']}/{evaluation_result['summary']['total_tests']}")
        log.info(f"結果已保存: {result_file}")
        log.info(f"{'='*60}\n")
        
        return evaluation_result
    
    async def compare_models(
        self,
        model1_name: str,
        model2_name: str,
        model_type: str
    ) -> Dict[str, Any]:
        """
        對比兩個模型
        
        Args:
            model1_name: 第一個模型名稱
            model2_name: 第二個模型名稱
            model_type: 模型類型
        
        Returns:
            對比結果
        """
        log.info(f"{'='*60}")
        log.info(f"開始對比模型")
        log.info(f"  模型1: {model1_name}")
        log.info(f"  模型2: {model2_name}")
        log.info(f"{'='*60}\n")
        
        # 評估兩個模型
        result1 = await self.evaluate_model(model1_name, model_type)
        result2 = await self.evaluate_model(model2_name, model_type)
        
        # 對比結果
        comparison = {
            "model1": {
                "name": model1_name,
                "score": result1.get("total_score", 0),
                "pass_rate": result1.get("pass_rate", 0)
            },
            "model2": {
                "name": model2_name,
                "score": result2.get("total_score", 0),
                "pass_rate": result2.get("pass_rate", 0)
            },
            "winner": model1_name if result1.get("total_score", 0) > result2.get("total_score", 0) else model2_name,
            "score_diff": abs(result1.get("total_score", 0) - result2.get("total_score", 0))
        }
        
        log.info(f"\n{'='*60}")
        log.info(f"🏆 對比結果")
        log.info(f"{'='*60}")
        log.info(f"模型1 ({model1_name}):")
        log.info(f"  總分: {comparison['model1']['score']:.1f}")
        log.info(f"  通過率: {comparison['model1']['pass_rate']*100:.1f}%")
        log.info(f"\n模型2 ({model2_name}):")
        log.info(f"  總分: {comparison['model2']['score']:.1f}")
        log.info(f"  通過率: {comparison['model2']['pass_rate']*100:.1f}%")
        log.info(f"\n勝者: {comparison['winner']}")
        log.info(f"分數差: {comparison['score_diff']:.1f}")
        log.info(f"{'='*60}\n")
        
        return comparison


def main():
    parser = argparse.ArgumentParser(description="評估Fine-Tuned模型")
    parser.add_argument(
        "--model",
        choices=["expert", "scammer"],
        help="模型類型"
    )
    parser.add_argument(
        "--model-name",
        help="要評估的模型名稱"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("MODEL1", "MODEL2"),
        help="對比兩個模型"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量評估所有訓練過的模型"
    )
    
    args = parser.parse_args()
    
    evaluator = ModelEvaluator()
    
    # 運行評估
    if args.compare:
        # 對比模式
        model_type = args.model or "expert"
        asyncio.run(evaluator.compare_models(args.compare[0], args.compare[1], model_type))
    
    elif args.batch:
        # 批量評估
        log.info("批量評估模式尚未完全實現")
        # TODO: 讀取training_history.json並評估所有模型
    
    elif args.model_name and args.model:
        # 單一評估
        asyncio.run(evaluator.evaluate_model(args.model_name, args.model))
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

