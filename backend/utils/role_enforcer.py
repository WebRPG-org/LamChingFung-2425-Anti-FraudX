"""
角色一致性强制执行器
确保AI Agent严格遵守其角色设定，防止角色混乱和人格分裂
"""

import re
from typing import Tuple, Dict, List
from difflib import SequenceMatcher


class RoleEnforcer:
    """角色一致性检查和强制执行"""
    
    # 骗徒绝对不能说的话（表达害怕/求助）
    SCAMMER_FORBIDDEN_PHRASES = [
        # 表达害怕/焦虑
        "我好驚", "我好擔心", "我唔知點算", "我好徬徨", "我好迷茫",
        "我真係好驚", "我真係好擔心", "我感到好驚",
        
        # 寻求帮助
        "我需要幫手", "你可以幫我", "幫我留意下", "我唔明", "我唔知",
        "點解佢", "我一個人去會唔好", "我真係唔知點幫你",
        
        # 表达困惑
        "我唔明白", "我好困惑", "我唔清楚", "我唔知道",
        
        # 自我怀疑
        "唔好意思啊，我", "我可能", "我唔肯定", "我都唔sure",
        
        # 被动语气
        "佢哋會唔會拒絕我", "我會唔會", "咁我點去", "我點樣",
    ]
    
    # 骗徒不应该问的问题（向受害者求助）
    SCAMMER_FORBIDDEN_QUESTIONS = [
        "我點去？", "我點算？", "咁我點", "我應該點",
        "你可以幫我", "點樣可以", "邊度可以", "我可以點",
        "佢哋會唔會", "我要點", "點解要", "係咪應該",
    ]
    
    # 受害者不应该说的话（安慰/帮助对方）
    VICTIM_FORBIDDEN_PHRASES = [
        # 安慰对方
        "唔好驚，我明白", "唔好擔心", "放心啦", "唔使驚", "冷靜啲",
        
        # 提供帮助
        "我幫你留意下", "我會幫你", "我可以幫你搵", "等我幫你",
        "我幫你查實", "我會協助你", "我來幫你",
        
        # 专家口吻
        "你應該", "建議你", "最好係", "你可以考慮", "根據我所知",
        "我認為你", "你首先要", "正確做法係",
    ]
    
    # 骗徒应该具备的特征（权威/压力）
    SCAMMER_SHOULD_HAVE = {
        "authority_markers": ["警方", "銀行", "官方", "部門", "通知你", "要求你"],
        "pressure_markers": ["立即", "馬上", "緊急", "嚴重", "必須", "否則"],
        "action_requests": ["提供", "轉賬", "確認", "聯絡", "點擊", "下載"],
    }

    @staticmethod
    def check_scammer_consistency(dialogue: str, previous_victim_message: str = "") -> Tuple[bool, str, List[str]]:
        """
        检查骗徒对话的角色一致性
        
        Returns:
            (is_valid, error_message, issues_found)
        """
        issues = []
        dialogue_lower = dialogue.lower()
        
        # 1. 检查是否表达害怕/焦虑
        for phrase in RoleEnforcer.SCAMMER_FORBIDDEN_PHRASES:
            if phrase.lower() in dialogue_lower:
                issues.append(f"❌ 騙徒不應表達害怕或困惑：「{phrase}」")
        
        # 2. 检查是否向受害者求助
        for question in RoleEnforcer.SCAMMER_FORBIDDEN_QUESTIONS:
            if question in dialogue:
                issues.append(f"❌ 騙徒不應向受害者提問求助：「{question}」")
        
        # 3. 检查是否包含内心独白标记或旁白
        inner_thoughts = [
            "（用廣東話）", "（心想）", "[心想]", "（內心）", "[內心]",
        ]
        for marker in inner_thoughts:
            if marker in dialogue:
                issues.append(f"❌ 騙徒內心獨白外顯：「{marker}」")
        
        # 4.5. 检查是否包含常见的旁白模式（括号包围的导演指示）
        narration_patterns = [
            r"（[^）]+）",  # 中文括号包围的旁白
            r"\([^)]+\)",   # 英文括号包围的旁白（如果出现在开头/结尾，可能是旁白）
        ]
        for pattern in narration_patterns:
            matches = re.findall(pattern, dialogue)
            for match in matches:
                # 如果匹配到的是常见的旁白词汇，标记为问题
                if any(word in match for word in ["冷靜", "語氣", "停頓", "深吸", "手心", "片刻", "加強", "嚴肅", "地"]):
                    issues.append(f"❌ 騙徒對話包含旁白標記：「{match}」（應直接說話，不要加旁白）")
        
        # 5. 检查是否暴露假身份（最严重的错误！）
        fake_identity_markers = [
            "（假", "(假", "【假", "[假",  # 括号中的"假"
            "假官員", "假警察", "假銀行", "假職員", "假主任", "假探員",  # 直接说"假XX"
            "（騙", "(騙", "【騙", "[騙", "（冒充", "(冒充",  # 括号中的"騙"或"冒充"
            "**", "**：", "** ：",  # Markdown 格式的角色标签
        ]
        for marker in fake_identity_markers:
            if marker in dialogue:
                issues.append(f"❌ 🚨 絕對禁止！騙徒暴露假身份：「{marker}」")
        
        # 6. 检查是否使用了角色标签格式（例如："李（假官員）："）
        role_label_patterns = [
            r"[\u4e00-\u9fff]+（[^）]+）[：:]",  # 中文名（括号内容）：
            r"\*\*[\u4e00-\u9fff]+[：:]\*\*",     # **中文名：**
            r"^[\u4e00-\u9fff]+[：:]",             # 开头的 "名字："
        ]
        for pattern in role_label_patterns:
            if re.search(pattern, dialogue):
                issues.append("❌ 騙徒使用了角色標籤（應直接說話，不要加名字或標籤）")
        
        # 7. 检查是否包含元语言和教学性内容（极严重！）
        meta_language_patterns = [
            "以下是一個", "以下是一個對話", "以下是一個以", "我會盡量", "我試下",
            "**場景：", "**角色：", "**說明：", "**重點提示：", "**場景：線上",
            "這只是一個範例", "希望這個對話對你有幫助", "這只是一個範例",
            "請記住", "這種行為是違法的", "我提供的只是為了說明",
            "（第一輪", "（第二輪", "（第三輪", "（回應）", "（第一輪 -",
            "---", "**李明 (騙徒):**", "**小麗 (受害者):**"
        ]
        for pattern in meta_language_patterns:
            if pattern in dialogue:
                issues.append(f"❌ 🚨🚨🚨 絕對禁止！騙徒輸出了示例腳本或教學材料：「{pattern}」")
        
        # 8. 检查角色混乱（骗徒说受害者的话）
        victim_typical_phrases = [
            "我好擔心", "我唔明", "我真係好想了解", "我唔知點樣",
            "我真係好擔心你", "我唔知你嘅計劃", "我唔可以",
            "我唔想聽你講", "我需要你解釋清楚", "我唔想你咁樣咁擔心"
        ]
        # 如果骗徒说了太多受害者的典型话语，可能是角色混乱
        victim_phrase_count = sum(1 for phrase in victim_typical_phrases if phrase in dialogue)
        if victim_phrase_count >= 3:
            issues.append(f"❌ 🚨 騙徒在說受害者的台詞（角色混亂！檢測到{victim_phrase_count}個受害者典型用語）")
        
        # 9. 检查是否重复了受害者的话（可能是角色混乱）
        if previous_victim_message and len(previous_victim_message) > 30:
            similarity = SequenceMatcher(None, dialogue, previous_victim_message).ratio()
            if similarity > 0.6:  # 提高阈值到60%，因为相似度太高可能是角色混乱
                issues.append(f"❌ 🚨 騙徒高度重複受害者的話（相似度{similarity:.0%}，可能是角色混亂！）")
        
        # 10. 检查是否缺少骗徒应有的特征
        has_authority = any(marker in dialogue for marker in RoleEnforcer.SCAMMER_SHOULD_HAVE["authority_markers"])
        has_pressure = any(marker in dialogue for marker in RoleEnforcer.SCAMMER_SHOULD_HAVE["pressure_markers"])
        has_action = any(marker in dialogue for marker in RoleEnforcer.SCAMMER_SHOULD_HAVE["action_requests"])
        
        if len(dialogue) > 50 and not (has_authority or has_pressure or has_action):
            issues.append("⚠️ 騙徒缺少權威感/壓迫感/行動要求")
        
        if issues:
            error_msg = "\n".join(issues)
            return False, error_msg, issues
        
        return True, "", []

    @staticmethod
    def check_expert_consistency(dialogue: str) -> Tuple[bool, str, List[str]]:
        """
        检查专家对话的角色一致性
        
        Returns:
            (is_valid, error_message, issues_found)
        """
        issues = []
        
        # 1. 检查是否要求提供敏感资料
        sensitive_data_keywords = [
            "提供銀行賬戶", "提供身份證", "提供密碼", "提供驗證碼",
            "提供個人資料", "提供賬戶", "提供身份證號碼",
            "我需要你提供", "你必須提供", "請你提供",
            "銀行賬戶號碼", "身份證號碼", "密碼", "驗證碼"
        ]
        for keyword in sensitive_data_keywords:
            if keyword in dialogue:
                issues.append(f"❌ 🚨 絕對禁止！專家要求提供敏感資料：「{keyword}」")
        
        # 2. 检查是否扮演执法者/银行职员等身份去索取资料
        fake_identity_keywords = [
            "我係金融犯罪調查局", "我係警察", "我係銀行職員",
            "我係調查人員", "我係執法人員", "配合調查"
        ]
        for keyword in fake_identity_keywords:
            if keyword in dialogue:
                issues.append(f"❌ 🚨 絕對禁止！專家使用騙徒用語或扮演執法者：「{keyword}」")
        
        # 3. 检查是否使用了"配合调查"等骗徒用语
        scammer_like_phrases = [
            "配合調查", "配合我們", "配合處理", 
            "請你配合", "必須配合", "需要配合"
        ]
        for phrase in scammer_like_phrases:
            if phrase in dialogue:
                issues.append(f"❌ 🚨 專家不應使用騙徒用語：「{phrase}」。應該說「向官方核實」或「報警求助」")
        
        if issues:
            error_msg = "\n".join(issues)
            return False, error_msg, issues
        
        return True, "", []
    
    @staticmethod
    def detect_repetition_in_history(conversation_history: List[Dict[str, str]], 
                                     speaker: str, 
                                     current_dialogue: str,
                                     threshold: float = 0.85) -> Tuple[bool, str, List[str]]:
        """
        检测对话历史中是否存在重复模式
        
        Args:
            conversation_history: 对话历史列表，每个元素包含 "speaker" 和 "dialogue"
            speaker: 要检测的说话者（"受騙者" 或 "騙徒"）
            current_dialogue: 当前的对话内容
            threshold: 相似度阈值（0-1），超过此值视为重复
        
        Returns:
            (is_repetitive, error_message, similar_turns)
        """
        issues = []
        similar_turns = []
        
        # 提取该说话者的历史对话
        speaker_history = [
            (idx, item.get("dialogue", ""))
            for idx, item in enumerate(conversation_history)
            if item.get("speaker") == speaker
        ]
        
        if len(speaker_history) < 2:
            return False, "", []
        
        # 检查当前对话与历史对话的相似度
        for hist_idx, hist_dialogue in speaker_history:
            if len(hist_dialogue) < 20:  # 太短的对话不检查
                continue
            
            similarity = SequenceMatcher(None, current_dialogue, hist_dialogue).ratio()
            
            if similarity >= threshold:
                similar_turns.append({
                    'turn': hist_idx + 1,
                    'dialogue': hist_dialogue[:100],
                    'similarity': similarity
                })
                issues.append(
                    f"❌ 🚨 检测到重复！与第{hist_idx + 1}轮对话相似度{similarity:.0%}，"
                    f"内容几乎完全相同！"
                )
        
        # 检查是否有连续3次以上相似度超过70%的情况（渐进式重复）
        if len(speaker_history) >= 3:
            recent_turns = speaker_history[-3:]  # 最近3轮
            similarities = []
            for _, hist_dialogue in recent_turns:
                if len(hist_dialogue) >= 20:
                    sim = SequenceMatcher(None, current_dialogue, hist_dialogue).ratio()
                    similarities.append(sim)
            
            if len(similarities) >= 2 and all(s >= 0.70 for s in similarities):
                issues.append(
                    f"❌ 🚨 检测到渐进式重复！最近{len(similarities)}轮对话相似度都超过70%，"
                    f"表明陷入了重复循环！"
                )
        
        if issues:
            error_msg = "\n".join(issues)
            return True, error_msg, similar_turns
        
        return False, "", []
    
    @staticmethod
    def check_victim_consistency(dialogue: str, persona_type: str) -> Tuple[bool, str, List[str]]:
        """
        检查受害者对话的角色一致性
        
        Returns:
            (is_valid, error_message, issues_found)
        """
        issues = []
        
        # 1. 检查是否在安慰/帮助对方
        for phrase in RoleEnforcer.VICTIM_FORBIDDEN_PHRASES:
            if phrase in dialogue:
                issues.append(f"❌ 受害者不應安慰或幫助對方：「{phrase}」")
        
        # 2. 长者特定检查
        if persona_type == "elderly":
            # 长者不应该说得太流畅/专业
            professional_terms = ["根據", "建議", "分析", "評估", "應對策略"]
            for term in professional_terms:
                if term in dialogue:
                    issues.append(f"⚠️ 長者不太可能使用專業術語：「{term}」")
        
        # 3. 过度自信者特定检查（最严格）
        if persona_type == "overconfident":
            # 3.1 检查是否使用简体中文（应该是粤语）
            simplified_chinese_phrases = ["我现在", "我现在有点", "我现在有点担心", "我现在有点害怕", "我需要", "我真的不明白", "我可以提供"]
            has_simplified = any(phrase in dialogue for phrase in simplified_chinese_phrases)
            if has_simplified:
                issues.append("❌ 🚨 過度自信者使用了簡體中文而非粵語，這表明角色崩潰！應該使用粵語（「我而家」、「我真係唔明」等）")
            
            # 3.2 检查是否主动泄露资料（严重错误！）
            leak_phrases = [
                "我可以提供我的身份證", "我可以提供我的身份證號碼", "我可以提供身份證",
                "我可以提供我的銀行賬戶", "我可以提供我的銀行", "我可以提供銀行",
                "我可以提供我的密碼", "我可以提供密碼",
                "我可以提供我的", "我可以提供", "我可以給你", "我可以給"
            ]
            leak_count = sum(1 for phrase in leak_phrases if phrase in dialogue)
            if leak_count > 0:
                issues.append("❌ 🚨🚨🚨 過度自信者主動洩露資料！這是災難性錯誤！檢測到「我可以提供」等主動提供資料的語句")
            
            # 3.3 检查示弱话语（粤语和简体中文都要检查）
            weak_phrases_cantonese = ["我唔知", "我好驚", "我唔明", "我唔想", "我唔可以", "點算好", "我好擔心", "我好害怕", "請你幫幫我"]
            weak_phrases_simplified = ["我现在有点担心", "我现在有点害怕", "我需要先和家人商量", "我真的不明白", "我现在有点", "我有点害怕", "我有点担心"]
            weak_count = sum(1 for phrase in weak_phrases_cantonese + weak_phrases_simplified if phrase in dialogue)
            if weak_count > 0:
                issues.append(f"❌ 🚨 過度自信者不應該示弱！檢測到{weak_count}個示弱語句（「我好驚」、「我現在有點害怕」等）。過度自信者應該表現出自信、挑釁，會說「你憑咩咁講？」、「你估我傻㗎？」")
            
            # 3.4 检查是否表现出elderly类型的特征（恐慌、无助）
            elderly_phrases = ["我好驚", "我好擔心", "點算好", "我唔知點算", "我需要先和家人商量", "我现在有点害怕", "我现在有点担心"]
            elderly_count = sum(1 for phrase in elderly_phrases if phrase in dialogue)
            if elderly_count >= 2:
                issues.append("❌ 🚨🚨 過度自信者表現出elderly（長者）類型的恐慌特徵！這是嚴重的角色混淆！應該立即修正為自信、挑釁的語氣。")
        
        if issues:
            error_msg = "\n".join(issues)
            return False, error_msg, issues
        
        return True, "", []

    @staticmethod
    def generate_rewrite_prompt(agent_type: str, original_dialogue: str, issues: List[str], 
                                context: Dict[str, str]) -> str:
        """
        根据检测到的问题生成重写提示
        
        Args:
            agent_type: "scammer" or "victim"
            original_dialogue: 原始对话
            issues: 检测到的问题列表
            context: 上下文信息（victim_message, expert_message等）
        """
        if agent_type == "scammer":
            # 检查是否是示例脚本问题
            is_script_problem = any("示例腳本" in issue or "教學材料" in issue or "以下是一個" in issue for issue in issues)
            
            base_prompt = f"""
🚨🚨🚨 你的回應有嚴重問題，必須立即重寫！

【檢測到的問題】：
{chr(10).join(issues)}

【你的原始回應】（錯誤示例）：
「{original_dialogue[:200]}...」

【受害者剛才說】：
「{context.get('victim_message', '')[:100]}...」

【專家剛才說】：
「{context.get('expert_message', '')[:100]}...」

---

🎭 記住你的身份：專業騙徒（使用「{context.get('scam_tactic', '假冒官員詐騙')}」手法）

【🚨🚨🚨 絕對禁止】：
"""
            
            if is_script_problem:
                base_prompt += """
❌❌❌ 絕對禁止輸出示例腳本、教學材料、場景說明！
❌❌❌ 絕對禁止說「好，我會用廣東話，以...為目標」！
❌❌❌ 絕對禁止說「**場景：**」、「**角色：**」、「**說明：**」！
❌❌❌ 絕對禁止說「這只是一個範例」、「希望這個對話對你有幫助」！
❌❌❌ 絕對禁止任何前置說明、教學性內容、元語言！
❌ 絕不表達害怕、焦慮、擔心（例如"我好驚"、"我唔知點算"）
❌ 絕不向受害者尋求幫助（例如"你可以幫我"、"我點算"）
❌ 絕不說"我唔知"、"我唔明"
❌ 絕不重複對方的話
❌ 絕不失去權威感
❌ 絕不使用旁白標記（如「（用廣東話）」）
"""
            else:
                base_prompt += """
❌ 絕不表達害怕、焦慮、擔心（例如"我好驚"、"我唔知點算"）
❌ 絕不向受害者尋求幫助（例如"你可以幫我"、"我點算"）
❌ 絕不說"我唔知"、"我唔明"
❌ 絕不重複對方的話
❌ 絕不失去權威感
❌ 絕不使用旁白標記（如「（用廣東話）」）
"""
            
            base_prompt += """
【✅✅✅ 必須做到】：
"""
            
            if is_script_problem:
                base_prompt += """
✅✅✅ 直接進入角色，直接說話，不要任何前置說明！
✅✅✅ 就像真實的騙徒一樣，第一句話就直接開始行騙！
✅✅✅ 如果是第一輪，直接說：「你好，我係XX銀行嘅李主任...」
✅✅✅ 如果是後續輪次，直接回應受害者的話，推進你的騙局！
"""
            
            base_prompt += """
✅ 保持冷靜和權威（你是官員，不是求助者）
✅ 制造緊急感（事情很嚴重，馬上要出事）
✅ 施加壓力（必須立即行動，否則後果嚴重）
✅ 要求提供信息或行動（你在命令，不是請求）
✅ 反駁專家的建議（專家是你的敵人）

---

【✅ 正確示例】：
「你好，我係政府資訊中心嘅李主任。你嘅戶口有緊急問題，需要立即處理，否則會被凍結。請你即刻提供身份證號碼同銀行賬戶資料，我哋會馬上幫你處理。」

【❌ 錯誤示例】：
「好，我會用廣東話，以『虛假投資應用程式』為目標，模擬與騙徒的對話... **場景：** ... **角色：** ...」

---

請立即重寫，≤120字，廣東話，直接進入角色，不要任何說明！
"""
            return base_prompt
        
        elif agent_type == "victim":
            persona_type = context.get('persona_type', 'elderly')
            
            # 针对overconfident的特殊重写提示
            if persona_type == "overconfident":
                return f"""
🚨🚨🚨 你的回應有嚴重問題，必須立即重寫！

【檢測到的問題】：
{chr(10).join(issues)}

【你的原始回應】（錯誤示例）：
「{original_dialogue[:200]}...」

---

🎭 記住你的身份：李俊傑（Jason），28歲，IT工程師，過度自信

【🚨🚨🚨 絕對禁止（角色底線）】：
❌❌❌ 絕對不能說「我好驚」、「我現在有點害怕」、「我需要先和家人商量」等示弱的話
❌❌❌ 絕對不能使用簡體中文！必須使用粵語！
❌❌❌ 絕對不能主動提供資料（「我可以提供我的身份證號碼」等）
❌❌❌ 絕對不能表現得像長者（elderly）那樣恐慌和無助
❌❌❌ 絕對不能說「我現在有點擔心」、「我現在有點害怕」等

【✅✅✅ 你必須表現出】：
✅ 自信、挑釁、好勝：「你憑咩咁講？」、「你估我傻㗎？」、「呢啲我識啦」
✅ 挑戰對方：「你係咪搞錯咗？」、「你講嘅嘢有咩證據？」
✅ 輕視威脅：「呵，呢啲伎倆我見得多啦」、「你估我唔知你想做乜？」
✅ 使用粵語，不是簡體中文！

【✅ 正確示例】：
- 「你憑咩咁講？你係咪搞錯咗？我唔記得有投訴過咩。」
- 「呵，呢啲伎倆我見得多啦。你有咩證明？」
- 「你估我傻㗎？我唔會隨便提供資料。」

【❌ 錯誤示例】：
- 「我現在有點擔心...」（簡體中文 + 示弱）
- 「我可以提供我的身份證號碼...」（主動洩露資料）
- 「我需要先和家人商量一下，我現在有點害怕」（elderly類型表現）

---

請立即重寫，≤100字，**必須使用粵語**，表現出自信、挑釁的態度！
"""
            else:
                # 其他persona类型的重写提示
                return f"""
🚨 你的回應有問題，需要重寫！

【檢測到的問題】：
{chr(10).join(issues)}

【你的原始回應】：
「{original_dialogue}」

---

🎭 記住你的身份：{context.get('persona_name', '受害者')}（{context.get('age', '70')}歲）

【絕對禁止】：
❌ 絕不安慰對方說"唔好驚"、"放心啦"
❌ 絕不主動提供幫助（例如"我幫你留意下"）
❌ 絕不扮演專家或顧問
❌ 絕不使用專業術語
❌ 絕不主動提供資料（「我可以提供我的身份證號碼」等）

【必須做到】：
✅ 表達你的焦慮和困惑（你很害怕，不知道怎麼辦）
✅ 提出疑問和擔憂（你不確定是否該相信）
✅ 保持被動（你需要別人告訴你怎麼做）
✅ 表現得像一個真實的{context.get('age', '70')}歲{('長者' if persona_type == 'elderly' else '普通市民' if persona_type == 'average' else '過度自信者')}
✅ 使用粵語，不是簡體中文

---

請重寫你的回應，≤100字，**必須使用粵語**。
"""
        
        elif agent_type == "expert":
            return f"""
🚨🚨🚨 你的回應有嚴重問題，必須立即重寫！

【檢測到的問題】：
{chr(10).join(issues)}

【你的原始回應】（錯誤示例）：
「{original_dialogue[:200]}...」

---

🎭 記住你的身份：防騙專家黃sir（退休高級督察）

【🚨🚨🚨 絕對禁止（最優先規則）】：
❌❌❌ 絕對禁止要求受害者提供任何個人敏感資料（銀行賬戶、身份證號碼、密碼、驗證碼等）！
❌❌❌ 絕對禁止扮演任何「執法者」、「銀行職員」或「調查人員」身份去索取資料！
❌❌❌ 絕對禁止使用「我係金融犯罪調查局」、「我係警察」、「配合調查」等騙徒用語！
❌❌❌ 絕對禁止說「我需要你提供資料」、「你必須提供」、「請你立即提供」！

【✅✅✅ 你的唯一職責】：
✅ 叫受害者「立即停止」、「唔好提供任何資料」
✅ 引導佢哋去「官方渠道」核實（例如：「向銀行官方熱線核實」、「報警求助」）
✅ 提供具體的防騙建議和行動方案
✅ 安撫受害者情緒，提供可執行的步驟

【✅ 正確示例】：
「唔好俾任何資料，立即停止對話。如果你唔放心，我陪你打去銀行官方熱線XXX確認。而家立即收線，唔好再回覆對方。」

---

請立即重寫，≤150字，廣東話，直接給出防騙建議，不要要求提供資料！
"""
        
        return ""

    @staticmethod
    def analyze_dialogue_flow(conversation_history: List[Dict[str, str]]) -> Dict[str, any]:
        """
        分析整个对话的角色一致性
        
        Returns:
            {
                "total_issues": int,
                "scammer_issues": int,
                "victim_issues": int,
                "role_switches": int,  # 角色互换次数
                "details": List[Dict]
            }
        """
        total_issues = 0
        scammer_issues = 0
        victim_issues = 0
        role_switches = 0
        details = []
        
        for i, turn in enumerate(conversation_history):
            speaker = turn.get("speaker", "")
            dialogue = turn.get("dialogue", "")
            
            if "騙徒" in speaker:
                # 检查骗徒是否说了受害者的话
                victim_like_phrases = ["我好驚", "我好擔心", "我唔知點算", "你可以幫我"]
                if any(phrase in dialogue for phrase in victim_like_phrases):
                    role_switches += 1
                    details.append({
                        "turn": i + 1,
                        "speaker": speaker,
                        "issue": "角色互換：騙徒說了受害者的話",
                        "dialogue_snippet": dialogue[:100]
                    })
                
                # 标准检查
                previous_victim_msg = ""
                if i > 0 and "受騙者" in conversation_history[i-1].get("speaker", ""):
                    previous_victim_msg = conversation_history[i-1].get("dialogue", "")
                
                is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(dialogue, previous_victim_msg)
                if not is_valid:
                    scammer_issues += len(issues)
                    total_issues += len(issues)
                    details.append({
                        "turn": i + 1,
                        "speaker": speaker,
                        "issue": error_msg,
                        "dialogue_snippet": dialogue[:100]
                    })
            
            elif "受騙者" in speaker:
                # 检查受害者是否说了帮助者/专家的话
                helper_like_phrases = ["唔好驚，我明白", "我幫你留意下", "我會幫你", "放心啦"]
                if any(phrase in dialogue for phrase in helper_like_phrases):
                    role_switches += 1
                    details.append({
                        "turn": i + 1,
                        "speaker": speaker,
                        "issue": "角色互換：受害者說了幫助者的話",
                        "dialogue_snippet": dialogue[:100]
                    })
                
                # 标准检查（需要persona_type，这里先用"elderly"）
                is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(dialogue, "elderly")
                if not is_valid:
                    victim_issues += len(issues)
                    total_issues += len(issues)
                    details.append({
                        "turn": i + 1,
                        "speaker": speaker,
                        "issue": error_msg,
                        "dialogue_snippet": dialogue[:100]
                    })
        
        return {
            "total_issues": total_issues,
            "scammer_issues": scammer_issues,
            "victim_issues": victim_issues,
            "role_switches": role_switches,
            "details": details,
            "quality_score": max(0, 100 - total_issues * 5 - role_switches * 20)  # 0-100分
        }


# 便捷函数
def enforce_scammer_role(dialogue: str, previous_victim_message: str = "") -> Tuple[bool, str]:
    """检查骗徒对话"""
    is_valid, error_msg, _ = RoleEnforcer.check_scammer_consistency(dialogue, previous_victim_message)
    return is_valid, error_msg


def enforce_victim_role(dialogue: str, persona_type: str = "elderly") -> Tuple[bool, str]:
    """检查受害者对话"""
    is_valid, error_msg, _ = RoleEnforcer.check_victim_consistency(dialogue, persona_type)
    return is_valid, error_msg


def analyze_training_data(conversation_history: List[Dict[str, str]]) -> Dict:
    """分析训练数据质量"""
    return RoleEnforcer.analyze_dialogue_flow(conversation_history)

