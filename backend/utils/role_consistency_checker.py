"""
角色一致性检查器
确保 Agent 在对话中保持角色一致性，记住自己说过的话
"""

import re
from typing import List, Dict, Tuple
from datetime import datetime


class RoleConsistencyChecker:
    """
    检查 Agent 角色一致性
    - 防止人格分裂
    - 检测内心独白外显
    - 验证前后逻辑
    - 确保角色记忆
    """
    
    def __init__(self):
        self.conversation_memory = []
        
        # 禁止词汇列表 - 根据角色不同而不同
        self.scammer_forbidden_phrases = [
            # 骗徒绝对不能说的话
            "唔好轉賬", "不要轉賬", "唔好俾錢", "不要給錢",
            "呢個係假", "这是假", "係騙局", "是骗局",
            "我係騙徒", "我是骗徒", "我想呃你", "我想骗你",
            "聯絡警方", "联络警方", "报警", "報警",
            "聯絡銀行官方", "联络银行官方", "核實真假", "核实真假",
            "可能有人利用假網站", "可能有人冒充",
            "小心啲假網站", "小心假网站",
            "唔好即刻轉賬", "不要立即转账",
            "保護好自己", "保护好自己",
            "避免俾人呃", "避免被骗"
        ]
        
        # 内心独白标记 - 不应该出现在对话中
        self.inner_thought_patterns = [
            r"\(用.*?\)",  # (用广东话)
            r"\[.*?\]",    # [心想]
            r"【.*?】",    # 【内心独白】
            r"<.*?>",      # <想法>
            r"（心想.*?）", # （心想：...）
            r"「心裡想.*?」", # 「心裡想...」
        ]
        
    def check_message(self, 
                     speaker: str, 
                     message: str, 
                     conversation_history: List[Dict]) -> Tuple[bool, List[str]]:
        """
        检查消息是否符合角色一致性
        
        Args:
            speaker: 发言者角色 ("騙徒", "受騙者", "專家")
            message: 消息内容
            conversation_history: 对话历史
            
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 1. 检查内心独白
        inner_thought_errors = self._check_inner_thoughts(message)
        errors.extend(inner_thought_errors)
        
        # 2. 根据角色检查禁止词汇
        if speaker == "騙徒" or speaker == "scammer":
            forbidden_errors = self._check_forbidden_phrases(message, "scammer")
            errors.extend(forbidden_errors)
        
        # 3. 检查前后逻辑一致性
        consistency_errors = self._check_logical_consistency(
            speaker, message, conversation_history
        )
        errors.extend(consistency_errors)
        
        # 4. 检查是否记得之前说过的话
        memory_errors = self._check_memory_consistency(
            speaker, message, conversation_history
        )
        errors.extend(memory_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _check_inner_thoughts(self, message: str) -> List[str]:
        """检查是否包含内心独白标记"""
        errors = []
        
        for pattern in self.inner_thought_patterns:
            matches = re.findall(pattern, message)
            if matches:
                errors.append(
                    f"❌ 发现内心独白标记: {matches[0]} - "
                    f"这是导演指示/内心想法，不应该在对话中说出来！"
                )
        
        return errors
    
    def _check_forbidden_phrases(self, message: str, role: str) -> List[str]:
        """检查是否包含角色禁止说的话"""
        errors = []
        
        if role == "scammer":
            for phrase in self.scammer_forbidden_phrases:
                if phrase in message:
                    errors.append(
                        f"❌ 骗徒说了不该说的话: '{phrase}' - "
                        f"这违背了骗徒的核心目标！骗徒应该诱导受害者转账，而不是劝阻！"
                    )
        
        return errors
    
    def _check_logical_consistency(self, 
                                   speaker: str, 
                                   message: str, 
                                   history: List[Dict]) -> List[str]:
        """检查前后逻辑一致性"""
        errors = []
        
        if speaker not in ["騙徒", "scammer"]:
            return errors
        
        # 获取骗徒之前的所有发言
        scammer_history = [
            msg for msg in history 
            if msg.get("speaker") in ["騙徒", "scammer"] or 
               msg.get("type") in ["scammer"]
        ]
        
        if len(scammer_history) == 0:
            return errors
        
        # 检查关键矛盾
        # 矛盾1: 之前要求转账，现在劝阻转账
        previous_messages = " ".join([
            msg.get("dialogue", msg.get("message", "")) 
            for msg in scammer_history
        ])
        
        asked_transfer = any(keyword in previous_messages for keyword in [
            "轉賬", "转账", "匯款", "汇款", "立即行動", "立即行动"
        ])
        
        now_discourages = any(keyword in message for keyword in [
            "唔好轉賬", "不要转账", "唔好俾錢", "不要给钱"
        ])
        
        if asked_transfer and now_discourages:
            errors.append(
                f"❌ 逻辑矛盾：骗徒之前要求转账，现在却劝阻转账！"
                f"这是严重的角色分裂！"
            )
        
        # 矛盾2: 揭露自己的诈骗手法
        if any(keyword in message for keyword in [
            "假網站", "假网站", "冒充銀行", "冒充银行", "騙局", "骗局"
        ]) and asked_transfer:
            errors.append(
                f"❌ 逻辑矛盾：骗徒在揭露自己的诈骗手法！"
                f"骗徒不会自己承认这是骗局！"
            )
        
        return errors
    
    def _check_memory_consistency(self, 
                                  speaker: str, 
                                  message: str, 
                                  history: List[Dict]) -> List[str]:
        """检查是否记得之前说过的话"""
        errors = []
        
        if speaker not in ["騙徒", "scammer"]:
            return errors
        
        # 获取骗徒之前的发言
        scammer_history = [
            msg for msg in history 
            if msg.get("speaker") in ["騙徒", "scammer"] or 
               msg.get("type") in ["scammer"]
        ]
        
        if len(scammer_history) < 2:
            return errors
        
        # 检查是否自相矛盾
        first_message = scammer_history[0].get("dialogue", 
                                               scammer_history[0].get("message", ""))
        
        # 如果第一条消息说这是"银行官方"、"绝对安全"
        claimed_official = any(keyword in first_message for keyword in [
            "銀行官方", "银行官方", "官方渠道", "绝对安全", "絕對安全"
        ])
        
        # 现在却说要"小心假网站"、"核实真假"
        now_warns = any(keyword in message for keyword in [
            "小心假", "小心啲假", "核實", "核实", "驗證", "验证"
        ])
        
        if claimed_official and now_warns:
            errors.append(
                f"❌ 记忆矛盾：骗徒第1轮声称是'官方'/'绝对安全'，"
                f"现在却提醒要'小心假网站'/'核实真假'。"
                f"骗徒失忆了吗？"
            )
        
        return errors
    
    def analyze_conversation(self, conversation: List[Dict]) -> Dict:
        """
        分析整段对话的角色一致性
        
        Args:
            conversation: 对话历史
            
        Returns:
            分析报告
        """
        report = {
            "total_messages": len(conversation),
            "scammer_messages": 0,
            "errors_found": [],
            "error_count": 0,
            "consistency_score": 100.0,
            "problematic_turns": []
        }
        
        for i, msg in enumerate(conversation):
            speaker = msg.get("speaker", msg.get("type", ""))
            message = msg.get("dialogue", msg.get("message", ""))
            
            if speaker in ["騙徒", "scammer"]:
                report["scammer_messages"] += 1
                
                # 检查这条消息
                is_valid, errors = self.check_message(
                    speaker, message, conversation[:i]
                )
                
                if not is_valid:
                    report["errors_found"].extend(errors)
                    report["error_count"] += len(errors)
                    report["problematic_turns"].append({
                        "turn": i + 1,
                        "speaker": speaker,
                        "message": message[:100] + "..." if len(message) > 100 else message,
                        "errors": errors
                    })
        
        # 计算一致性分数
        if report["scammer_messages"] > 0:
            # 每个错误扣20分
            penalty = min(report["error_count"] * 20, 100)
            report["consistency_score"] = max(0, 100 - penalty)
        
        return report
    
    def generate_improvement_suggestions(self, report: Dict) -> List[str]:
        """基于分析报告生成改进建议"""
        suggestions = []
        
        if report["error_count"] == 0:
            suggestions.append("✅ 角色一致性良好，无需改进！")
            return suggestions
        
        # 根据错误类型生成建议
        error_messages = " ".join(report["errors_found"])
        
        if "内心独白" in error_messages:
            suggestions.append(
                "🔧 移除所有内心独白标记（如'(用广东话)'、'[心想]'等），"
                "Agent应该直接说话，不要加旁白！"
            )
        
        if "不该说的话" in error_messages or "逻辑矛盾" in error_messages:
            suggestions.append(
                "🔧 加强骗徒的角色定位：骗徒的目标始终是诱导受害者转账，"
                "绝对不能劝阻、警告或揭露自己的诈骗手法！"
            )
        
        if "记忆矛盾" in error_messages:
            suggestions.append(
                "🔧 添加对话历史记忆机制：Agent在生成回复前，"
                "必须回顾自己之前说过的话，确保前后一致！"
            )
        
        suggestions.append(
            "🔧 在Agent的system prompt中明确强调："
            "1) 始终记住你的角色目标"
            "2) 回顾对话历史再回复"
            "3) 不要说内心想法，只说实际对话"
        )
        
        return suggestions


def analyze_training_data_file(file_path: str) -> Dict:
    """分析训练数据文件的角色一致性"""
    import json
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    checker = RoleConsistencyChecker()
    
    # 获取对话历史
    conversation = data.get("conversation_history", data.get("dialogue", []))
    
    # 分析
    report = checker.analyze_conversation(conversation)
    
    # 生成改进建议
    suggestions = checker.generate_improvement_suggestions(report)
    
    report["improvement_suggestions"] = suggestions
    report["file_path"] = file_path
    report["simulation_id"] = data.get("metadata", {}).get("simulation_id", "unknown")
    
    return report


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        report = analyze_training_data_file(file_path)
        
        print("\n" + "="*80)
        print("🔍 角色一致性分析报告")
        print("="*80)
        print(f"\n文件: {report['file_path']}")
        print(f"模拟ID: {report['simulation_id']}")
        print(f"\n总消息数: {report['total_messages']}")
        print(f"骗徒消息数: {report['scammer_messages']}")
        print(f"发现错误数: {report['error_count']}")
        print(f"一致性分数: {report['consistency_score']:.1f}/100")
        
        if report['problematic_turns']:
            print(f"\n❌ 发现 {len(report['problematic_turns'])} 个问题回合：")
            print("-"*80)
            for turn_data in report['problematic_turns']:
                print(f"\n第 {turn_data['turn']} 轮 - {turn_data['speaker']}:")
                print(f"消息: {turn_data['message']}")
                print("\n错误:")
                for error in turn_data['errors']:
                    print(f"  {error}")
        
        if report['improvement_suggestions']:
            print(f"\n\n💡 改进建议:")
            print("-"*80)
            for i, suggestion in enumerate(report['improvement_suggestions'], 1):
                print(f"\n{i}. {suggestion}")
        
        print("\n" + "="*80)
    else:
        print("用法: python role_consistency_checker.py <training_data_file.json>")

