"""
自动化训练流程 - 将进化知识应用到模型
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

ARMS_RACE_DIR = os.path.join(os.path.dirname(__file__), '..', 'arms_race_data')
SCAMMER_EVOLUTION_DIR = os.path.join(ARMS_RACE_DIR, 'scammer_evolution')
EXPERT_EVOLUTION_DIR = os.path.join(ARMS_RACE_DIR, 'expert_evolution')
MODEL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')


class ModelUpdater:
    """模型更新器 - 应用进化知识更新Agent"""
    
    def __init__(self):
        self.scammer_agent_path = os.path.join(os.path.dirname(__file__), '..', 'agents', 'scammer.py')
        self.expert_agent_path = os.path.join(os.path.dirname(__file__), '..', 'agents', 'expert.py')
        self.backup_dir = os.path.join(os.path.dirname(__file__), '..', 'agents', 'backups')
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_latest_evolution_data(self, agent_type: str) -> Dict[str, Any]:
        """获取最新的进化数据"""
        if agent_type == 'scammer':
            evolution_dir = SCAMMER_EVOLUTION_DIR
        else:
            evolution_dir = EXPERT_EVOLUTION_DIR
        
        if not os.path.exists(evolution_dir):
            log.warning(f"进化数据目录不存在: {evolution_dir}")
            return {}
        
        # 找到最新的进化文件
        files = [f for f in os.listdir(evolution_dir) if f.endswith('.json')]
        if not files:
            log.warning("没有找到进化数据")
            return {}
        
        latest_file = sorted(files)[-1]
        filepath = os.path.join(evolution_dir, latest_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        log.info(f"加载 {agent_type} 的最新进化数据: {latest_file}")
        return data
    
    def backup_agent(self, agent_path: str):
        """备份Agent文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        agent_name = os.path.basename(agent_path).replace('.py', '')
        backup_path = os.path.join(self.backup_dir, f'{agent_name}_backup_{timestamp}.py')
        
        with open(agent_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log.info(f"已备份: {backup_path}")
        return backup_path
    
    def update_scammer_agent(self, evolution_data: Dict[str, Any]):
        """更新骗徒Agent"""
        log.info("开始更新骗徒Agent...")
        
        # 备份现有Agent
        self.backup_agent(self.scammer_agent_path)
        
        # 读取当前Agent文件
        with open(self.scammer_agent_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到instruction的位置并更新
        training_instructions = evolution_data.get('training_instructions', '')
        
        # 在instruction末尾添加进化学习内容
        evolution_section = f"""

## 🎓 进化学习 (第 {evolution_data.get('generation', 1)} 代)

{training_instructions}
"""
        
        # 找到instruction定义的位置
        in_instruction = False
        instruction_start = -1
        instruction_end = -1
        triple_quote_count = 0
        
        for i, line in enumerate(lines):
            if 'instruction = """' in line:
                instruction_start = i
                in_instruction = True
                triple_quote_count = 1
            elif in_instruction and '"""' in line:
                triple_quote_count += 1
                if triple_quote_count == 2:
                    instruction_end = i
                    break
        
        if instruction_start != -1 and instruction_end != -1:
            # 在instruction结束前插入进化内容
            lines.insert(instruction_end, evolution_section + '\n')
            
            # 写回文件
            with open(self.scammer_agent_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            log.info("✅ 骗徒Agent已更新")
        else:
            log.error("❌ 未找到instruction定义位置")
    
    def update_expert_agent(self, evolution_data: Dict[str, Any]):
        """更新专家Agent"""
        log.info("开始更新专家Agent...")
        
        # 备份现有Agent
        self.backup_agent(self.expert_agent_path)
        
        # 读取当前Agent文件
        with open(self.expert_agent_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到base_instruction的位置并更新
        training_instructions = evolution_data.get('training_instructions', '')
        
        # 在instruction末尾添加进化学习内容
        evolution_section = f"""

## 🎓 进化学习 (第 {evolution_data.get('generation', 1)} 代)

{training_instructions}
"""
        
        # 找到base_instruction定义的位置
        in_instruction = False
        instruction_start = -1
        instruction_end = -1
        triple_quote_count = 0
        
        for i, line in enumerate(lines):
            if 'base_instruction = """' in line:
                instruction_start = i
                in_instruction = True
                triple_quote_count = 1
            elif in_instruction and '"""' in line:
                triple_quote_count += 1
                if triple_quote_count == 2:
                    instruction_end = i
                    break
        
        if instruction_start != -1 and instruction_end != -1:
            # 在instruction结束前插入进化内容
            lines.insert(instruction_end, evolution_section + '\n')
            
            # 写回文件
            with open(self.expert_agent_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            log.info("✅ 专家Agent已更新")
        else:
            log.error("❌ 未找到base_instruction定义位置")
    
    def create_evolution_report(self, scammer_data: Dict, expert_data: Dict) -> str:
        """创建进化报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(MODEL_OUTPUT_DIR, f'evolution_applied_{timestamp}.md')
        
        report = f"""# Agent进化应用报告

## 更新时间
{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

## 骗徒进化 (第 {scammer_data.get('generation', 'N/A')} 代)

### 学习到的教训
"""
        for i, point in enumerate(scammer_data.get('learning_points', []), 1):
            report += f"\n**{i}. {point.get('lesson', '')}**\n"
            report += f"- 反制策略: {point.get('counter_strategy', '')}\n"
        
        report += "\n### 进阶战术\n"
        for i, tactic in enumerate(scammer_data.get('advanced_tactics', []), 1):
            report += f"\n**{i}. {tactic.get('base_tactic', '')}** (进化等级 {tactic.get('evolution_level', '')})\n"
        
        report += f"\n\n## 专家进化 (第 {expert_data.get('generation', 'N/A')} 代)\n\n### 识别的弱点\n"
        
        for i, point in enumerate(expert_data.get('learning_points', []), 1):
            report += f"\n**{i}. {point.get('identified_weakness', '')}**\n"
            report += f"- 改进策略: {point.get('improvement_strategy', '')}\n"
        
        report += "\n### 反制战术\n"
        for i, tactic in enumerate(expert_data.get('counter_tactics', []), 1):
            report += f"\n**{i}. 针对: {tactic.get('target_tactic', '')}**\n"
        
        report += """

## 下一步

1. **测试更新后的Agent**
   - 运行: python start_server.py
   - 启动服务测试

2. **运行多轮模拟**
   - 测试不同的victim persona
   - 观察专家胜率变化
   - 收集新的training data

3. **评估进化效果**
   - 对比更新前后的表现
   - 分析新策略的有效性
   - 记录意外行为

4. **继续迭代**
   - 收集足够新数据后
   - 再次运行arms_race_system.py
   - 进行下一代进化

## 注意事项

- 原始Agent已备份到 agents/backups/
- 如需回滚，从备份恢复即可
- 建议先小范围测试再全面部署
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        log.info(f"进化报告已生成: {report_path}")
        return report_path


def main():
    """主函数"""
    log.info("🤖 自动化训练流程启动")
    log.info("="*60)
    
    updater = ModelUpdater()
    
    # 1. 获取最新进化数据
    log.info("📥 步骤1: 加载进化数据...")
    scammer_evolution = updater.get_latest_evolution_data('scammer')
    expert_evolution = updater.get_latest_evolution_data('expert')
    
    if not scammer_evolution or not expert_evolution:
        log.error("❌ 未找到进化数据，请先运行 arms_race_system.py")
        return
    
    # 2. 更新Agent
    log.info("\n🔧 步骤2: 更新Agent...")
    updater.update_scammer_agent(scammer_evolution)
    updater.update_expert_agent(expert_evolution)
    
    # 3. 生成报告
    log.info("\n📝 步骤3: 生成进化报告...")
    report_path = updater.create_evolution_report(scammer_evolution, expert_evolution)
    
    # 总结
    log.info("\n" + "="*60)
    log.info("✅ 自动化训练完成！")
    log.info("="*60)
    log.info("📊 更新统计:")
    log.info(f"  - 骗徒进化代数: {scammer_evolution.get('generation', 'N/A')}")
    log.info(f"  - 专家进化代数: {expert_evolution.get('generation', 'N/A')}")
    log.info(f"  - 备份位置: {updater.backup_dir}")
    log.info(f"  - 进化报告: {report_path}")
    log.info("\n🎯 下一步:")
    log.info("1. python start_server.py  # 启动服务测试")
    log.info("2. 运行多轮模拟收集数据")
    log.info("3. python scripts/arms_race_system.py  # 下一代进化")
    log.info("="*60 + "\n")


if __name__ == "__main__":
    main()

