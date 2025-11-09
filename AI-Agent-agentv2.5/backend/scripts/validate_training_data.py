"""
训练数据验证工具
检查训练数据的角色一致性，标记和移动无效数据
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.role_enforcer import RoleEnforcer
from utils.logger import log


class TrainingDataValidator:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            data_dir = os.path.join(base_dir, 'training_data')
        
        self.data_dir = Path(data_dir)
        self.invalid_dir = self.data_dir / 'invalid'
        self.valid_dir = self.data_dir / 'validated'
        self.report_dir = self.data_dir / 'validation_reports'
        
        # 创建目录
        self.invalid_dir.mkdir(exist_ok=True)
        self.valid_dir.mkdir(exist_ok=True)
        self.report_dir.mkdir(exist_ok=True)
    
    def validate_file(self, file_path: Path) -> Dict:
        """验证单个训练数据文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation_history = data.get('conversation_history', [])
            if not conversation_history:
                return {
                    "file": file_path.name,
                    "valid": False,
                    "reason": "空对话历史",
                    "quality_score": 0
                }
            
            # 使用RoleEnforcer分析对话
            analysis = RoleEnforcer.analyze_dialogue_flow(conversation_history)
            
            # 判定标准
            is_valid = (
                analysis['role_switches'] == 0 and  # 没有角色互换
                analysis['quality_score'] >= 60  # 质量分数>=60
            )
            
            return {
                "file": file_path.name,
                "valid": is_valid,
                "quality_score": analysis['quality_score'],
                "total_issues": analysis['total_issues'],
                "scammer_issues": analysis['scammer_issues'],
                "victim_issues": analysis['victim_issues'],
                "role_switches": analysis['role_switches'],
                "total_turns": len(conversation_history),
                "details": analysis['details']
            }
        
        except Exception as e:
            log.error(f"验证文件失败: {file_path.name} - {e}")
            return {
                "file": file_path.name,
                "valid": False,
                "reason": f"处理错误: {str(e)}",
                "quality_score": 0
            }
    
    def validate_all(self, move_invalid: bool = False) -> Dict:
        """验证所有训练数据文件"""
        json_files = list(self.data_dir.glob('training_data_*.json'))
        
        if not json_files:
            log.warning(f"未找到训练数据文件: {self.data_dir}")
            return {"total": 0, "valid": 0, "invalid": 0, "results": []}
        
        log.info(f"找到 {len(json_files)} 个训练数据文件")
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for file_path in json_files:
            log.info(f"验证: {file_path.name}")
            result = self.validate_file(file_path)
            results.append(result)
            
            if result['valid']:
                valid_count += 1
                if move_invalid:  # 如果启用移动，把有效的移到validated目录
                    dest = self.valid_dir / file_path.name
                    shutil.copy2(file_path, dest)
                    log.info(f"  ✅ 有效（质量分数: {result['quality_score']}）-> {dest}")
            else:
                invalid_count += 1
                log.warning(f"  ❌ 无效（质量分数: {result.get('quality_score', 0)}）")
                log.warning(f"     原因: {result.get('reason', '角色一致性问题')}")
                
                if move_invalid:
                    dest = self.invalid_dir / file_path.name
                    shutil.move(str(file_path), str(dest))
                    log.warning(f"     已移动到: {dest}")
        
        summary = {
            "total": len(json_files),
            "valid": valid_count,
            "invalid": invalid_count,
            "valid_percentage": (valid_count / len(json_files) * 100) if json_files else 0,
            "results": results
        }
        
        return summary
    
    def generate_report(self, summary: Dict) -> str:
        """生成验证报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.report_dir / f'validation_report_{timestamp}.md'
        
        # 按质量分数排序
        sorted_results = sorted(summary['results'], key=lambda x: x.get('quality_score', 0), reverse=True)
        
        report_content = f"""# 训练数据验证报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 总体统计

- **总文件数**: {summary['total']}
- **有效文件**: {summary['valid']} ({summary['valid_percentage']:.1f}%)
- **无效文件**: {summary['invalid']} ({100-summary['valid_percentage']:.1f}%)

---

## 🏆 高质量对话（质量分数 >= 80）

"""
        high_quality = [r for r in sorted_results if r.get('quality_score', 0) >= 80]
        if high_quality:
            for r in high_quality:
                report_content += f"- ✅ `{r['file']}` - 质量分数: {r['quality_score']}\n"
        else:
            report_content += "（无）\n"
        
        report_content += f"""

---

## ⚠️ 中等质量对话（60 <= 质量分数 < 80）

"""
        medium_quality = [r for r in sorted_results if 60 <= r.get('quality_score', 0) < 80]
        if medium_quality:
            for r in medium_quality:
                report_content += f"- ⚠️ `{r['file']}` - 质量分数: {r['quality_score']}\n"
                report_content += f"  - 问题数: {r.get('total_issues', 0)}, 角色互换: {r.get('role_switches', 0)}\n"
        else:
            report_content += "（无）\n"
        
        report_content += f"""

---

## ❌ 低质量对话（质量分数 < 60）- 建议删除

"""
        low_quality = [r for r in sorted_results if r.get('quality_score', 0) < 60]
        if low_quality:
            for r in low_quality:
                report_content += f"- ❌ `{r['file']}` - 质量分数: {r['quality_score']}\n"
                report_content += f"  - 问题数: {r.get('total_issues', 0)}, 角色互换: {r.get('role_switches', 0)}\n"
                
                # 显示部分问题详情
                details = r.get('details', [])[:3]  # 只显示前3个问题
                for detail in details:
                    report_content += f"    - 第{detail['turn']}轮: {detail['issue'][:80]}...\n"
        else:
            report_content += "（无）\n"
        
        report_content += f"""

---

## 📈 问题类型统计

"""
        # 统计各类问题
        scammer_issues_total = sum(r.get('scammer_issues', 0) for r in sorted_results)
        victim_issues_total = sum(r.get('victim_issues', 0) for r in sorted_results)
        role_switches_total = sum(r.get('role_switches', 0) for r in sorted_results)
        
        report_content += f"""
- **骗徒角色问题**: {scammer_issues_total}
- **受害者角色问题**: {victim_issues_total}
- **角色互换次数**: {role_switches_total}

---

## 💡 建议

"""
        if summary['valid_percentage'] < 50:
            report_content += """
🚨 **严重警告**：超过50%的训练数据存在角色一致性问题！

**建议立即采取的行动**：
1. ✅ 停止使用低质量数据进行模型训练
2. ✅ 修复 `scammer.py` 和 `victim.py` 的prompt设计
3. ✅ 在 `simulation_routes.py` 中集成 `role_enforcer`
4. ✅ 重新生成训练数据

"""
        elif summary['valid_percentage'] < 80:
            report_content += """
⚠️ **警告**：部分训练数据存在质量问题。

**建议**：
1. 移除或修复低质量数据
2. 加强角色一致性检查
3. 考虑微调agent的prompt

"""
        else:
            report_content += """
✅ **良好**：大部分训练数据质量合格。

**建议**：
1. 继续监控新生成的数据
2. 定期运行验证工具
3. 关注边缘case的处理

"""
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        log.info(f"验证报告已生成: {report_path}")
        return str(report_path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='验证训练数据的角色一致性')
    parser.add_argument('--data-dir', type=str, help='训练数据目录路径')
    parser.add_argument('--move', action='store_true', help='移动无效文件到invalid目录')
    parser.add_argument('--file', type=str, help='验证单个文件')
    
    args = parser.parse_args()
    
    validator = TrainingDataValidator(args.data_dir)
    
    if args.file:
        # 验证单个文件
        file_path = Path(args.file)
        if not file_path.exists():
            log.error(f"文件不存在: {file_path}")
            return
        
        result = validator.validate_file(file_path)
        print(f"\n文件: {result['file']}")
        print(f"有效性: {'✅ 有效' if result['valid'] else '❌ 无效'}")
        print(f"质量分数: {result.get('quality_score', 0)}")
        print(f"问题数: {result.get('total_issues', 0)}")
        print(f"角色互换: {result.get('role_switches', 0)}")
        
        if not result['valid'] and result.get('details'):
            print("\n问题详情:")
            for detail in result['details'][:5]:  # 只显示前5个
                print(f"  - 第{detail['turn']}轮: {detail['issue']}")
    else:
        # 验证所有文件
        print("\n" + "="*80)
        print("🔍 开始验证训练数据...")
        print("="*80 + "\n")
        
        summary = validator.validate_all(move_invalid=args.move)
        
        print("\n" + "="*80)
        print("📊 验证完成")
        print("="*80)
        print(f"总文件数: {summary['total']}")
        print(f"有效文件: {summary['valid']} ({summary['valid_percentage']:.1f}%)")
        print(f"无效文件: {summary['invalid']} ({100-summary['valid_percentage']:.1f}%)")
        
        if args.move:
            print(f"\n无效文件已移动到: {validator.invalid_dir}")
            print(f"有效文件已复制到: {validator.valid_dir}")
        
        # 生成报告
        report_path = validator.generate_report(summary)
        print(f"\n详细报告: {report_path}")


if __name__ == "__main__":
    main()

