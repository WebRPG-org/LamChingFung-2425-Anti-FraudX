"""
模型版本管理系统 - 管理Agent的不同版本并支持A/B测试
"""

import os
import json
import sys
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

AGENTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'agents')
VERSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'agent_versions')
AB_TEST_DIR = os.path.join(os.path.dirname(__file__), '..', 'ab_test_results')


class AgentVersionManager:
    """Agent版本管理器"""
    
    def __init__(self):
        self.ensure_directories()
        self.versions_metadata_path = os.path.join(VERSIONS_DIR, 'versions_metadata.json')
        self.load_metadata()
    
    def ensure_directories(self):
        """确保目录存在"""
        for directory in [VERSIONS_DIR, AB_TEST_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                log.info(f"创建目录: {directory}")
        
        # 为每个agent类型创建子目录
        for agent_type in ['scammer', 'expert', 'victim', 'recorder']:
            agent_version_dir = os.path.join(VERSIONS_DIR, agent_type)
            if not os.path.exists(agent_version_dir):
                os.makedirs(agent_version_dir)
    
    def load_metadata(self):
        """加载版本元数据"""
        if os.path.exists(self.versions_metadata_path):
            with open(self.versions_metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'scammer': {},
                'expert': {},
                'victim': {},
                'recorder': {}
            }
    
    def save_metadata(self):
        """保存版本元数据"""
        with open(self.versions_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def create_version(self, agent_type: str, description: str = '', generation: int = 0) -> str:
        """创建新版本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_id = f"v{generation}_{timestamp}"
        
        # 复制当前agent文件
        source_file = os.path.join(AGENTS_DIR, f'{agent_type}.py')
        dest_dir = os.path.join(VERSIONS_DIR, agent_type)
        dest_file = os.path.join(dest_dir, f'{agent_type}_{version_id}.py')
        
        shutil.copy2(source_file, dest_file)
        
        # 更新元数据
        self.metadata[agent_type][version_id] = {
            'created_at': datetime.now().isoformat(),
            'description': description,
            'generation': generation,
            'file_path': dest_file,
            'status': 'active',
            'performance': {
                'total_simulations': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0
            }
        }
        
        self.save_metadata()
        log.info(f"✅ 创建新版本: {agent_type} {version_id}")
        return version_id
    
    def get_version(self, agent_type: str, version_id: str) -> Optional[Dict[str, Any]]:
        """获取版本信息"""
        return self.metadata.get(agent_type, {}).get(version_id)
    
    def list_versions(self, agent_type: str) -> List[Dict[str, Any]]:
        """列出所有版本"""
        versions = []
        for version_id, data in self.metadata.get(agent_type, {}).items():
            versions.append({
                'version_id': version_id,
                **data
            })
        # 按创建时间倒序排列
        versions.sort(key=lambda x: x['created_at'], reverse=True)
        return versions
    
    def get_latest_version(self, agent_type: str) -> Optional[str]:
        """获取最新版本ID"""
        versions = self.list_versions(agent_type)
        if versions:
            return versions[0]['version_id']
        return None
    
    def update_performance(self, agent_type: str, version_id: str, outcome: str):
        """更新性能统计"""
        if agent_type not in self.metadata or version_id not in self.metadata[agent_type]:
            log.warning(f"版本不存在: {agent_type} {version_id}")
            return
        
        perf = self.metadata[agent_type][version_id]['performance']
        perf['total_simulations'] += 1
        
        if outcome == 'SUCCESS':
            if agent_type == 'expert':
                perf['wins'] += 1
            else:  # scammer
                perf['losses'] += 1
        elif outcome == 'FAILURE':
            if agent_type == 'expert':
                perf['losses'] += 1
            else:  # scammer
                perf['wins'] += 1
        
        # 更新胜率
        if perf['total_simulations'] > 0:
            perf['win_rate'] = perf['wins'] / perf['total_simulations'] * 100
        
        self.save_metadata()
    
    def rollback_to_version(self, agent_type: str, version_id: str):
        """回滚到指定版本"""
        version_info = self.get_version(agent_type, version_id)
        if not version_info:
            log.error(f"版本不存在: {agent_type} {version_id}")
            return False
        
        source_file = version_info['file_path']
        dest_file = os.path.join(AGENTS_DIR, f'{agent_type}.py')
        
        # 备份当前版本
        backup_file = os.path.join(AGENTS_DIR, 'backups', 
                                    f'{agent_type}_before_rollback_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        shutil.copy2(dest_file, backup_file)
        
        # 恢复到指定版本
        shutil.copy2(source_file, dest_file)
        
        log.info(f"✅ 已回滚到版本: {agent_type} {version_id}")
        log.info(f"   备份位置: {backup_file}")
        return True
    
    def compare_versions(self, agent_type: str, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """对比两个版本"""
        v1 = self.get_version(agent_type, version_id1)
        v2 = self.get_version(agent_type, version_id2)
        
        if not v1 or not v2:
            log.error("版本不存在")
            return {}
        
        comparison = {
            'version_1': {
                'id': version_id1,
                'generation': v1.get('generation', 0),
                'created_at': v1.get('created_at', ''),
                'performance': v1.get('performance', {})
            },
            'version_2': {
                'id': version_id2,
                'generation': v2.get('generation', 0),
                'created_at': v2.get('created_at', ''),
                'performance': v2.get('performance', {})
            },
            'performance_diff': {
                'win_rate_diff': v2['performance']['win_rate'] - v1['performance']['win_rate'],
                'total_simulations_diff': v2['performance']['total_simulations'] - v1['performance']['total_simulations']
            }
        }
        
        return comparison


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self, version_manager: AgentVersionManager):
        self.version_manager = version_manager
        self.ab_tests = {}
        self.ab_test_metadata_path = os.path.join(AB_TEST_DIR, 'ab_tests_metadata.json')
        self.load_ab_tests()
    
    def load_ab_tests(self):
        """加载A/B测试数据"""
        if os.path.exists(self.ab_test_metadata_path):
            with open(self.ab_test_metadata_path, 'r', encoding='utf-8') as f:
                self.ab_tests = json.load(f)
        else:
            self.ab_tests = {}
    
    def save_ab_tests(self):
        """保存A/B测试数据"""
        with open(self.ab_test_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.ab_tests, f, ensure_ascii=False, indent=2)
    
    def create_ab_test(self, agent_type: str, version_a: str, version_b: str, 
                       description: str = '', target_simulations: int = 50) -> str:
        """创建A/B测试"""
        test_id = f"abtest_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.ab_tests[test_id] = {
            'agent_type': agent_type,
            'version_a': version_a,
            'version_b': version_b,
            'description': description,
            'target_simulations': target_simulations,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'results': {
                'version_a': {
                    'simulations': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0
                },
                'version_b': {
                    'simulations': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0
                }
            }
        }
        
        self.save_ab_tests()
        log.info(f"✅ 创建A/B测试: {test_id}")
        log.info(f"   对比版本: {version_a} vs {version_b}")
        return test_id
    
    def record_result(self, test_id: str, version: str, outcome: str):
        """记录测试结果"""
        if test_id not in self.ab_tests:
            log.warning(f"测试不存在: {test_id}")
            return
        
        test = self.ab_tests[test_id]
        agent_type = test['agent_type']
        
        if version not in ['version_a', 'version_b']:
            log.warning(f"无效的版本标识: {version}")
            return
        
        results = test['results'][version]
        results['simulations'] += 1
        
        # 对于expert，SUCCESS是win；对于scammer，FAILURE是win
        if agent_type == 'expert':
            if outcome == 'SUCCESS':
                results['wins'] += 1
            else:
                results['losses'] += 1
        else:  # scammer
            if outcome == 'FAILURE':
                results['wins'] += 1
            else:
                results['losses'] += 1
        
        # 更新胜率
        if results['simulations'] > 0:
            results['win_rate'] = results['wins'] / results['simulations'] * 100
        
        # 检查是否达到目标次数
        total_sims = (test['results']['version_a']['simulations'] + 
                     test['results']['version_b']['simulations'])
        if total_sims >= test['target_simulations']:
            test['status'] = 'completed'
            log.info(f"🎯 A/B测试完成: {test_id}")
        
        self.save_ab_tests()
    
    def get_test_report(self, test_id: str) -> Dict[str, Any]:
        """获取测试报告"""
        if test_id not in self.ab_tests:
            return {}
        
        test = self.ab_tests[test_id]
        results_a = test['results']['version_a']
        results_b = test['results']['version_b']
        
        # 计算统计显著性（简化版）
        win_rate_diff = results_b['win_rate'] - results_a['win_rate']
        
        # 判断胜者
        if win_rate_diff > 5:
            winner = 'version_b'
            confidence = 'high' if abs(win_rate_diff) > 10 else 'medium'
        elif win_rate_diff < -5:
            winner = 'version_a'
            confidence = 'high' if abs(win_rate_diff) > 10 else 'medium'
        else:
            winner = 'tie'
            confidence = 'low'
        
        report = {
            'test_id': test_id,
            'agent_type': test['agent_type'],
            'status': test['status'],
            'created_at': test['created_at'],
            'version_a': {
                'id': test['version_a'],
                **results_a
            },
            'version_b': {
                'id': test['version_b'],
                **results_b
            },
            'analysis': {
                'win_rate_diff': win_rate_diff,
                'winner': winner,
                'confidence': confidence,
                'recommendation': self._generate_recommendation(winner, confidence, win_rate_diff)
            }
        }
        
        return report
    
    def _generate_recommendation(self, winner: str, confidence: str, diff: float) -> str:
        """生成推荐建议"""
        if winner == 'tie':
            return "两个版本表现相近，建议继续收集更多数据或保持当前版本"
        
        if confidence == 'high':
            return f"强烈建议采用 {winner}，胜率提升 {abs(diff):.2f}%"
        elif confidence == 'medium':
            return f"建议采用 {winner}，但建议进行更多测试以确认"
        else:
            return "差异不显著，需要更多数据"
    
    def generate_comparison_report(self, test_id: str) -> str:
        """生成对比报告文件"""
        report_data = self.get_test_report(test_id)
        if not report_data:
            log.error(f"测试不存在: {test_id}")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(AB_TEST_DIR, f'report_{test_id}_{timestamp}.md')
        
        report = f"""# A/B测试报告

## 测试信息
- **测试ID**: {report_data['test_id']}
- **Agent类型**: {report_data['agent_type']}
- **测试状态**: {report_data['status']}
- **创建时间**: {report_data['created_at']}

## 版本对比

### Version A: {report_data['version_a']['id']}
- **模拟次数**: {report_data['version_a']['simulations']}
- **胜利次数**: {report_data['version_a']['wins']}
- **失败次数**: {report_data['version_a']['losses']}
- **胜率**: {report_data['version_a']['win_rate']:.2f}%

### Version B: {report_data['version_b']['id']}
- **模拟次数**: {report_data['version_b']['simulations']}
- **胜利次数**: {report_data['version_b']['wins']}
- **失败次数**: {report_data['version_b']['losses']}
- **胜率**: {report_data['version_b']['win_rate']:.2f}%

## 分析结果

- **胜率差异**: {report_data['analysis']['win_rate_diff']:.2f}%
- **胜者**: {report_data['analysis']['winner']}
- **置信度**: {report_data['analysis']['confidence']}

## 推荐建议

{report_data['analysis']['recommendation']}

## 详细数据

| 指标 | Version A | Version B | 差异 |
|------|-----------|-----------|------|
| 模拟次数 | {report_data['version_a']['simulations']} | {report_data['version_b']['simulations']} | {report_data['version_b']['simulations'] - report_data['version_a']['simulations']} |
| 胜率 | {report_data['version_a']['win_rate']:.2f}% | {report_data['version_b']['win_rate']:.2f}% | {report_data['analysis']['win_rate_diff']:.2f}% |
| 胜利次数 | {report_data['version_a']['wins']} | {report_data['version_b']['wins']} | {report_data['version_b']['wins'] - report_data['version_a']['wins']} |

## 下一步行动

"""
        
        if report_data['analysis']['winner'] == 'version_b' and report_data['analysis']['confidence'] == 'high':
            report += """
1. 将 Version B 部署为主要版本
2. 将 Version A 归档为历史版本
3. 继续监控 Version B 的表现
"""
        elif report_data['analysis']['winner'] == 'version_a' and report_data['analysis']['confidence'] == 'high':
            report += """
1. 保持 Version A 为主要版本
2. 分析 Version B 的问题
3. 考虑进一步改进 Version B
"""
        else:
            report += """
1. 继续收集更多数据
2. 考虑扩大测试规模
3. 分析两个版本的具体差异
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        log.info(f"对比报告已生成: {report_path}")
        return report_path


def main():
    """主函数 - 演示用法"""
    log.info("🎮 模型版本管理系统")
    log.info("="*60)
    
    manager = AgentVersionManager()
    ab_manager = ABTestManager(manager)
    
    # 列出所有版本
    print("\n📦 当前版本:")
    for agent_type in ['scammer', 'expert']:
        print(f"\n{agent_type.upper()}:")
        versions = manager.list_versions(agent_type)
        if versions:
            for v in versions[:5]:  # 只显示最新5个
                print(f"  - {v['version_id']} (代数: {v['generation']}, 胜率: {v['performance']['win_rate']:.2f}%)")
        else:
            print("  (无版本记录)")
    
    # 列出活跃的A/B测试
    print("\n🧪 活跃的A/B测试:")
    active_tests = [tid for tid, test in ab_manager.ab_tests.items() if test['status'] == 'active']
    if active_tests:
        for test_id in active_tests:
            test = ab_manager.ab_tests[test_id]
            print(f"  - {test_id}")
            print(f"    对比: {test['version_a']} vs {test['version_b']}")
            print(f"    进度: {test['results']['version_a']['simulations'] + test['results']['version_b']['simulations']}/{test['target_simulations']}")
    else:
        print("  (无活跃测试)")
    
    log.info("\n" + "="*60)
    log.info("💡 使用方法:")
    log.info("1. 创建版本: manager.create_version('expert', '第2代进化', generation=2)")
    log.info("2. A/B测试: ab_manager.create_ab_test('expert', 'v1_xxx', 'v2_xxx')")
    log.info("3. 回滚: manager.rollback_to_version('expert', 'v1_xxx')")


if __name__ == "__main__":
    main()

