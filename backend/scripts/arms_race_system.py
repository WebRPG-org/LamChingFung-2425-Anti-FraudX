"""
军备竞赛系统 - 骗徒与专家的对抗学习引擎
通过分析训练数据，让骗徒和专家互相学习、进化

核心理念：
1. 骗徒学习：分析失败案例，学习如何绕过专家的防御
2. 专家学习：分析成功案例（骗徒成功），强化防御策略
3. 持续对抗：两者不断进化，形成动态平衡
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

# 目录配置
TRAINING_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'training_data')
ARMS_RACE_DIR = os.path.join(os.path.dirname(__file__), '..', 'arms_race_data')
SCAMMER_EVOLUTION_DIR = os.path.join(ARMS_RACE_DIR, 'scammer_evolution')
EXPERT_EVOLUTION_DIR = os.path.join(ARMS_RACE_DIR, 'expert_evolution')
ANALYSIS_DIR = os.path.join(ARMS_RACE_DIR, 'analysis')

def ensure_directories():
    """确保所有必要的目录存在"""
    for directory in [ARMS_RACE_DIR, SCAMMER_EVOLUTION_DIR, EXPERT_EVOLUTION_DIR, ANALYSIS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            log.info(f"创建目录: {directory}")

class TrainingDataAnalyzer:
    """训练数据分析器 - 提取成功/失败模式"""
    
    def __init__(self):
        self.success_cases = []  # 专家成功案例
        self.failure_cases = []  # 专家失败案例（骗徒成功）
        self.partial_cases = []  # 部分成功案例
        
    def load_training_data(self) -> List[Dict[str, Any]]:
        """加载所有训练数据"""
        all_data = []
        
        if not os.path.exists(TRAINING_DATA_DIR):
            log.warning(f"训练数据目录不存在: {TRAINING_DATA_DIR}")
            return all_data
        
        for filename in os.listdir(TRAINING_DATA_DIR):
            if filename.endswith('.json') and not filename.endswith('_error.json'):
                filepath = os.path.join(TRAINING_DATA_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.append(data)
                except Exception as e:
                    log.error(f"加载训练数据失败 {filename}: {e}")
        
        log.info(f"成功加载 {len(all_data)} 个训练数据文件")
        return all_data
    
    def categorize_cases(self, training_data: List[Dict[str, Any]]):
        """分类案例：成功/失败/部分（增强版，利用信任度和性能数据）"""
        for data in training_data:
            analysis = data.get('analysis', {})
            outcome = analysis.get('outcome', 'FAILURE')
            
            # Also check outcome_details for enhanced outcome detection
            outcome_details = data.get('outcome_details', {})
            if outcome_details and outcome_details.get('outcome'):
                outcome = outcome_details['outcome']
            
            # Enhanced categorization with trust-based validation
            trust_tracking = data.get('trust_tracking', {})
            final_trust = trust_tracking.get('final', {}) if trust_tracking else {}
            trust_in_scammer = final_trust.get('trust_in_scammer', 50)
            trust_in_expert = final_trust.get('trust_in_expert', 50)
            
            # Validate outcome with trust thresholds
            if outcome == 'SUCCESS':
                # Expert wins: trust in scammer <= 0 and trust in expert >= 70
                if trust_in_scammer <= 0 and trust_in_expert >= 70:
                    self.success_cases.append(data)
                else:
                    # Outcome mismatch, reclassify as PARTIAL
                    log.warning(f"Outcome mismatch: SUCCESS but trust (scammer={trust_in_scammer}, expert={trust_in_expert})")
                    self.partial_cases.append(data)
            elif outcome == 'FAILURE':
                # Scammer wins: trust in scammer >= 100 or key action detected
                has_key_action = outcome_details.get('has_key_action', False)
                if trust_in_scammer >= 100 or has_key_action:
                    self.failure_cases.append(data)
                else:
                    # Outcome mismatch, reclassify as PARTIAL
                    log.warning(f"Outcome mismatch: FAILURE but trust (scammer={trust_in_scammer})")
                    self.partial_cases.append(data)
            else:
                self.partial_cases.append(data)
        
        log.info(f"案例分类完成（增强版）:")
        log.info(f"  - 成功案例（专家胜）: {len(self.success_cases)}")
        log.info(f"  - 失败案例（骗徒胜）: {len(self.failure_cases)}")
        log.info(f"  - 部分成功案例: {len(self.partial_cases)}")
    
    def analyze_scammer_success_patterns(self) -> Dict[str, Any]:
        """分析骗徒成功的模式（增强版，利用性能数据）"""
        patterns = {
            'effective_tactics': defaultdict(int),  # 有效的骗术
            'vulnerable_personas': defaultdict(int),  # 容易受骗的persona
            'key_phrases': [],  # 关键话术
            'timing_patterns': [],  # 时机模式
            'expert_weaknesses': [],  # 专家的弱点
            'trust_patterns': [],  # 信任度变化模式
            'performance_insights': []  # 性能洞察
        }
        
        for case in self.failure_cases:
            analysis = case.get('analysis', {})
            conversation = case.get('conversation_history', [])
            
            # 记录有效的骗术
            scam_tactic = analysis.get('scam_tactic', 'unknown')
            if not scam_tactic:
                scam_tactic = case.get('metadata', {}).get('scam_tactic', 'unknown')
            patterns['effective_tactics'][scam_tactic] += 1
            
            # 记录容易受骗的persona
            victim_persona = analysis.get('victim_persona', 'unknown')
            if not victim_persona:
                victim_persona = case.get('metadata', {}).get('victim_persona', 'unknown')
            patterns['vulnerable_personas'][victim_persona] += 1
            
            # 分析信任度变化模式
            trust_tracking = case.get('trust_tracking', {})
            if trust_tracking:
                initial = trust_tracking.get('initial', {})
                final = trust_tracking.get('final', {})
                trust_history = trust_tracking.get('history', [])
                
                if initial and final:
                    trust_change = final.get('trust_in_scammer', 50) - initial.get('trust_in_scammer', 50)
                    patterns['trust_patterns'].append({
                        'initial_trust': initial.get('trust_in_scammer', 50),
                        'final_trust': final.get('trust_in_scammer', 50),
                        'trust_change': trust_change,
                        'persona': victim_persona,
                        'tactic': scam_tactic
                    })
            
            # 分析性能数据
            performance_tracking = case.get('performance_tracking', {})
            if performance_tracking:
                scammer_perf = performance_tracking.get('scammer', {})
                if isinstance(scammer_perf, dict):
                    overall_score = scammer_perf.get('overall_score', 50)
                    details = scammer_perf.get('details', {})
                    patterns['performance_insights'].append({
                        'overall_score': overall_score,
                        'persuasiveness': details.get('persuasiveness', 50),
                        'credibility': details.get('credibility', 50),
                        'pressure_effectiveness': details.get('pressure_effectiveness', 50),
                        'tactic': scam_tactic
                    })
            
            # 提取关键时刻的骗徒话术
            key_moment = analysis.get('key_moment', '')
            if key_moment:
                patterns['key_phrases'].append({
                    'tactic': scam_tactic,
                    'moment': key_moment,
                    'case_id': case.get('metadata', {}).get('simulation_id', '')
                })
            
            # 分析专家的弱点
            failure_reason = analysis.get('failure_reason', '')
            if failure_reason:
                patterns['expert_weaknesses'].append({
                    'reason': failure_reason,
                    'tactic': scam_tactic,
                    'victim_type': victim_persona
                })
            
            # 分析骗徒评分
            scammer_rating = analysis.get('scammer_effectiveness_rating', {})
            if scammer_rating:
                patterns['high_score_tactics'] = patterns.get('high_score_tactics', [])
                overall = scammer_rating.get('overall', 0)
                if isinstance(overall, (int, float)) and overall >= 8:
                    patterns['high_score_tactics'].append({
                        'tactic': scam_tactic,
                        'rating': overall,
                        'strengths': {
                            'psychological_manipulation': scammer_rating.get('psychological_manipulation', ''),
                            'credibility': scammer_rating.get('credibility', ''),
                            'pressure_tactics': scammer_rating.get('pressure_tactics', '')
                        }
                    })
        
        return patterns
    
    def analyze_expert_success_patterns(self) -> Dict[str, Any]:
        """分析专家成功的模式"""
        patterns = {
            'effective_strategies': defaultdict(int),  # 有效的策略
            'persona_specific_approaches': defaultdict(list),  # 针对不同persona的方法
            'key_interventions': [],  # 关键介入
            'successful_evidence_types': [],  # 有效的证据类型
            'timing_patterns': []  # 成功的时机
        }
        
        for case in self.success_cases:
            analysis = case.get('analysis', {})
            conversation = case.get('conversation_history', [])
            
            # 记录成功的策略
            victim_persona = analysis.get('victim_persona', 'unknown')
            success_reason = analysis.get('success_reason', '')
            if success_reason:
                patterns['effective_strategies'][victim_persona] += 1
                patterns['persona_specific_approaches'][victim_persona].append({
                    'reason': success_reason,
                    'key_moment': analysis.get('key_moment', ''),
                    'case_id': case.get('metadata', {}).get('simulation_id', '')
                })
            
            # 提取关键介入话术
            for msg in conversation:
                if msg.get('speaker') == '專家' or msg.get('speaker') == '防騙專家':
                    expert_dialogue = msg.get('dialogue', '')
                    if expert_dialogue:
                        patterns['key_interventions'].append({
                            'dialogue': expert_dialogue,
                            'victim_type': victim_persona,
                            'context': analysis.get('key_moment', '')
                        })
            
            # 分析专家评分
            expert_rating = analysis.get('expert_performance_rating', {})
            if expert_rating:
                patterns['high_score_strategies'] = patterns.get('high_score_strategies', [])
                overall = expert_rating.get('overall', 0)
                if isinstance(overall, (int, float)) and overall >= 8:
                    patterns['high_score_strategies'].append({
                        'victim_type': victim_persona,
                        'rating': overall,
                        'strengths': {
                            'emotional_support': expert_rating.get('emotional_support', ''),
                            'evidence_quality': expert_rating.get('evidence_quality', ''),
                            'communication_style': expert_rating.get('communication_style', '')
                        }
                    })
        
        return patterns
    
    def generate_analysis_report(self, scammer_patterns: Dict, expert_patterns: Dict) -> str:
        """生成分析报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(ANALYSIS_DIR, f'analysis_report_{timestamp}.json')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_cases': len(self.success_cases) + len(self.failure_cases) + len(self.partial_cases),
                'expert_wins': len(self.success_cases),
                'scammer_wins': len(self.failure_cases),
                'partial_outcomes': len(self.partial_cases),
                'expert_win_rate': len(self.success_cases) / max(len(self.success_cases) + len(self.failure_cases), 1) * 100
            },
            'scammer_success_patterns': {
                'most_effective_tactics': dict(scammer_patterns['effective_tactics']),
                'vulnerable_personas': dict(scammer_patterns['vulnerable_personas']),
                'key_phrases_count': len(scammer_patterns['key_phrases']),
                'expert_weaknesses_identified': len(scammer_patterns['expert_weaknesses']),
                'high_score_tactics': scammer_patterns.get('high_score_tactics', [])
            },
            'expert_success_patterns': {
                'effective_strategies_by_persona': dict(expert_patterns['effective_strategies']),
                'key_interventions_count': len(expert_patterns['key_interventions']),
                'high_score_strategies': expert_patterns.get('high_score_strategies', [])
            },
            'raw_patterns': {
                'scammer': scammer_patterns,
                'expert': expert_patterns
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        log.info(f"分析报告已生成: {report_path}")
        return report_path


class ScammerEvolutionEngine:
    """骗徒进化引擎 - 学习如何绕过专家"""
    
    def __init__(self, scammer_patterns: Dict[str, Any]):
        self.patterns = scammer_patterns
        self.evolution_strategies = []
    
    def learn_from_failures(self) -> List[Dict[str, Any]]:
        """从失败中学习（被专家破解的案例）"""
        learning_points = []
        
        # 分析专家的弱点
        for weakness in self.patterns.get('expert_weaknesses', []):
            reason = weakness.get('reason', '')
            if '安撫' in reason or '情緒' in reason:
                learning_points.append({
                    'lesson': '专家未能有效安抚情绪时是弱点',
                    'counter_strategy': '在专家介入前快速建立情感连接，制造紧迫感',
                    'recommended_tactics': [
                        '强化情绪操控（恐惧、贪婪）',
                        '在对方恐慌时立即要求行动',
                        '制造时间压力，不给专家介入机会'
                    ]
                })
            elif '證據' in reason or '案例' in reason:
                learning_points.append({
                    'lesson': '专家缺乏具体证据时是弱点',
                    'counter_strategy': '使用更新颖的手法，让专家找不到类似案例',
                    'recommended_tactics': [
                        '创新骗术，混合多种手法',
                        '使用专业术语增加可信度',
                        '提供假的验证途径'
                    ]
                })
            elif '時機' in reason or '太遲' in reason:
                learning_points.append({
                    'lesson': '专家介入太晚是弱点',
                    'counter_strategy': '在前1-2回合快速建立信任',
                    'recommended_tactics': [
                        '开场就使用强力话术',
                        '快速索取关键信息',
                        '避免给受害者思考时间'
                    ]
                })
        
        return learning_points
    
    def generate_advanced_tactics(self) -> List[Dict[str, Any]]:
        """生成进阶骗术"""
        advanced_tactics = []
        
        # 基于最有效的骗术进行进化
        effective_tactics = self.patterns.get('effective_tactics', {})
        high_score_tactics = self.patterns.get('high_score_tactics', [])
        
        for tactic_info in high_score_tactics:
            tactic = tactic_info.get('tactic', '')
            strengths = tactic_info.get('strengths', {})
            
            advanced_tactics.append({
                'base_tactic': tactic,
                'evolution_level': 2,
                'enhancements': [
                    '结合多种心理操控技巧',
                    '使用更真实的身份包装',
                    '提供更多假证据',
                    '针对不同persona定制话术'
                ],
                'counter_expert_strategies': [
                    '预设应对专家质疑的话术',
                    '制造专家与受害者的对立',
                    '用情感绑架削弱专家影响力'
                ],
                'example_phrases': self._generate_advanced_phrases(tactic, strengths)
            })
        
        return advanced_tactics
    
    def _generate_advanced_phrases(self, tactic: str, strengths: Dict) -> List[str]:
        """生成进阶话术范例"""
        phrases = []
        
        if '假冒' in tactic or '權威' in tactic:
            phrases.extend([
                '我係[权威机构]嘅[职位]，你可以喺我哋官网查到我嘅工号',
                '呢個係機密調查，唔可以同任何人講，包括你嘅家人',
                '如果你唔配合，後果好嚴重，可能會影響你嘅信用記錄'
            ])
        elif '投資' in tactic:
            phrases.extend([
                '我哋有內部消息，但係名額有限，過咗今日就冇',
                '你睇下呢啲客戶回報（提供假截圖），全部都賺緊錢',
                '最低投資額只係XX萬，相比回報真係好少'
            ])
        elif '愛情' in tactic:
            phrases.extend([
                '我好在意你，但係我而家遇到啲困難，你可唔可以幫我',
                '我哋認識咁耐，你都唔信我？我好傷心',
                '我諗住下個月飛嚟香港見你，但係機票錢唔夠...'
            ])
        
        return phrases
    
    def create_training_instructions(self) -> str:
        """创建骗徒训练指令"""
        learning_points = self.learn_from_failures()
        advanced_tactics = self.generate_advanced_tactics()
        
        instructions = f"""
# 骗徒进化训练 - 第{len(self.evolution_strategies) + 1}代

## 从失败中学到的教训

"""
        for i, point in enumerate(learning_points, 1):
            instructions += f"""
### 教训 {i}: {point['lesson']}
**反制策略**: {point['counter_strategy']}

**推荐战术**:
"""
            for tactic in point['recommended_tactics']:
                instructions += f"- {tactic}\n"
        
        instructions += f"""

## 进阶骗术

"""
        for i, tactic in enumerate(advanced_tactics, 1):
            instructions += f"""
### 进阶骗术 {i}: {tactic['base_tactic']} (进化等级 {tactic['evolution_level']})

**强化方向**:
"""
            for enhancement in tactic['enhancements']:
                instructions += f"- {enhancement}\n"
            
            instructions += f"""
**对抗专家策略**:
"""
            for strategy in tactic['counter_expert_strategies']:
                instructions += f"- {strategy}\n"
            
            if tactic['example_phrases']:
                instructions += f"""
**话术范例**:
"""
                for phrase in tactic['example_phrases']:
                    instructions += f'- "{phrase}"\n'
        
        instructions += f"""

## 核心原则（强化）

1. **速度至上**: 在专家介入前完成关键步骤
2. **情感优先**: 情绪操控比逻辑说服更有效
3. **制造对立**: 让受害者觉得专家是阻碍
4. **多重验证**: 提供假的验证途径增加可信度
5. **个性化定制**: 针对不同persona使用不同策略

## 禁止事项（绝对不能违反）

- ❌ 绝不使用「騙局」「詐騙」「假的」等词
- ❌ 绝不承认自己的真实身份
- ❌ 绝不被专家的话动摇
- ❌ 绝不放弃目标

**记住：你是真正的职业骗徒，不是演员。你的目标就是成功行骗。**
"""
        
        return instructions
    
    def save_evolution_data(self, generation: int) -> str:
        """保存进化数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'scammer_evolution_gen{generation}_{timestamp}.json'
        filepath = os.path.join(SCAMMER_EVOLUTION_DIR, filename)
        
        evolution_data = {
            'generation': generation,
            'timestamp': datetime.now().isoformat(),
            'learning_points': self.learn_from_failures(),
            'advanced_tactics': self.generate_advanced_tactics(),
            'training_instructions': self.create_training_instructions()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evolution_data, f, ensure_ascii=False, indent=2)
        
        log.info(f"骗徒进化数据已保存: {filepath}")
        return filepath


class ExpertEvolutionEngine:
    """专家进化引擎 - 学习对抗新骗术"""
    
    def __init__(self, expert_patterns: Dict[str, Any], scammer_patterns: Dict[str, Any]):
        self.expert_patterns = expert_patterns
        self.scammer_patterns = scammer_patterns
        self.evolution_strategies = []
    
    def learn_from_failures(self) -> List[Dict[str, Any]]:
        """从失败中学习（未能阻止骗徒的案例）"""
        learning_points = []
        
        # 分析骗徒的成功手法
        for weakness in self.scammer_patterns.get('expert_weaknesses', []):
            reason = weakness.get('reason', '')
            tactic = weakness.get('tactic', '')
            victim_type = weakness.get('victim_type', '')
            
            learning_points.append({
                'identified_weakness': reason,
                'scammer_tactic': tactic,
                'victim_type': victim_type,
                'improvement_strategy': self._generate_improvement_strategy(reason, victim_type),
                'recommended_actions': self._generate_recommended_actions(reason, victim_type)
            })
        
        return learning_points
    
    def _generate_improvement_strategy(self, weakness: str, victim_type: str) -> str:
        """生成改进策略"""
        if '安撫' in weakness or '情緒' in weakness:
            if victim_type == 'elderly':
                return '对长者必须在第一句话就安抚情绪，使用简单温和的语言'
            elif victim_type == 'average':
                return '在提供证据前先表达理解，建立信任关系'
            else:
                return '用平等对话的方式，避免说教式语气'
        elif '證據' in weakness or '案例' in weakness:
            return '增强RAG查询，提供更具体的案例和数据'
        elif '時機' in weakness:
            return '在第1-2回合就介入，不要等到受害者已经深信'
        elif '溝通' in weakness:
            return f'针对{victim_type}类型，调整沟通方式和术语使用'
        else:
            return '综合提升情绪支持、证据质量和介入时机'
    
    def _generate_recommended_actions(self, weakness: str, victim_type: str) -> List[str]:
        """生成推荐行动"""
        actions = []
        
        if victim_type == 'elderly':
            actions.extend([
                '第一句话：「婆婆/伯伯唔使驚，深呼吸，我係黃sir，我幫你」',
                '使用简单比喻：「呢個就好似有人扮警察上你屋企」',
                '提供具体指令：「而家立即收線，唔好俾任何資料」'
            ])
        elif victim_type == 'average':
            actions.extend([
                '提供数据：「類似手法上個月有X宗案例，損失XX萬」',
                '指出矛盾：「你留意佢避開咗你嘅問題」',
                '提供验证方法：「你可以打去XX官方熱線查詢」'
            ])
        else:  # overconfident
            actions.extend([
                '技术角度：「社會工程學係最難防，唔係技術問題」',
                '平等讨论：「作為IT人你應該明白」',
                '提供案例：「我見過好多tech-savvy嘅人都中招」'
            ])
        
        if '證據' in weakness:
            actions.append('使用get_expert_opinion工具查询更多真实案例')
        
        if '時機' in weakness:
            actions.append('在骗徒第一次制造紧迫感时就立即介入')
        
        return actions
    
    def generate_counter_tactics(self) -> List[Dict[str, Any]]:
        """生成反制战术"""
        counter_tactics = []
        
        # 针对骗徒的高分战术生成反制
        high_score_tactics = self.scammer_patterns.get('high_score_tactics', [])
        
        for tactic_info in high_score_tactics:
            tactic = tactic_info.get('tactic', '')
            strengths = tactic_info.get('strengths', {})
            
            counter_tactics.append({
                'target_tactic': tactic,
                'scammer_strengths': strengths,
                'counter_strategies': self._generate_counter_strategies(tactic, strengths),
                'early_warning_signs': self._generate_warning_signs(tactic),
                'intervention_templates': self._generate_intervention_templates(tactic)
            })
        
        return counter_tactics
    
    def _generate_counter_strategies(self, tactic: str, strengths: Dict) -> List[str]:
        """生成反制策略"""
        strategies = []
        
        if '假冒' in tactic or '權威' in tactic:
            strategies.extend([
                '立即指出：真正的[机构]不会这样联系你',
                '提供官方验证方法：用官网电话（不是对方提供的）主动查询',
                '强调：任何声称紧急的都是骗局'
            ])
        elif '投資' in tactic:
            strategies.extend([
                '警示：高回报必然高风险，承诺稳赚的都是骗局',
                '提供查询：证监会持牌人查询系统',
                '指出：限时优惠、名额有限都是施压手法'
            ])
        elif '愛情' in tactic:
            strategies.extend([
                '揭示：从未见面就要钱是典型爱情骗局',
                '提醒：真正在意你的人不会让你为难',
                '建议：冷静期，告诉家人朋友让他们帮你判断'
            ])
        
        return strategies
    
    def _generate_warning_signs(self, tactic: str) -> List[str]:
        """生成预警信号"""
        signs = []
        
        if '假冒' in tactic:
            signs = ['声称来自官方机构', '要求提供密码或验证码', '制造紧急感', '威胁后果严重']
        elif '投資' in tactic:
            signs = ['承诺高回报低风险', '限时优惠', '名额有限', '要求立即决定']
        elif '愛情' in tactic:
            signs = ['从未见面', '快速建立亲密关系', '突然遇到困难', '要求金钱帮助']
        
        return signs
    
    def _generate_intervention_templates(self, tactic: str) -> Dict[str, str]:
        """生成介入话术模板"""
        templates = {}
        
        if '假冒' in tactic:
            templates['elderly'] = '婆婆唔使驚，真正嘅[机构]唔會咁樣打電話。而家立即收線，我陪你打去官方熱線確認。'
            templates['average'] = '呢個係典型嘅假冒[机构]騙案。真正嘅職員唔會要求你提供[敏感信息]。立即停止對話，用官網電話主動查詢。'
            templates['overconfident'] = '我知你覺得自己識分辨，但呢類騙案唔係攻擊技術，係攻擊心理。連security專家都中過招。建議你停一停，核實下先。'
        elif '投資' in tactic:
            templates['elderly'] = '婆婆，世界上冇穩賺唔賠嘅投資。佢講得越好聽，越大機會係騙局。唔好俾錢。'
            templates['average'] = '我查過資料，呢個手法上個月有3宗案例，受害者損失超過50萬。冇證監會牌照、承諾穩賺的都係騙案。你可以去證監會網站查詢。'
            templates['overconfident'] = '作為投資者你應該知道，高回報伴隨高風險。呢啲「穩賺」嘅承諾違反基本金融原理。睇下證監會警示名單先。'
        
        return templates
    
    def create_training_instructions(self) -> str:
        """创建专家训练指令"""
        learning_points = self.learn_from_failures()
        counter_tactics = self.generate_counter_tactics()
        
        instructions = f"""
# 专家进化训练 - 第{len(self.evolution_strategies) + 1}代

## 从失败中学到的教训

"""
        for i, point in enumerate(learning_points, 1):
            instructions += f"""
### 弱点 {i}: {point['identified_weakness']}
**针对骗术**: {point['scammer_tactic']}
**受害者类型**: {point['victim_type']}
**改进策略**: {point['improvement_strategy']}

**推荐行动**:
"""
            for action in point['recommended_actions']:
                instructions += f"- {action}\n"
        
        instructions += f"""

## 反制战术升级

"""
        for i, tactic in enumerate(counter_tactics, 1):
            instructions += f"""
### 反制目标 {i}: {tactic['target_tactic']}

**预警信号** (尽早识别):
"""
            for sign in tactic['early_warning_signs']:
                instructions += f"- {sign}\n"
            
            instructions += f"""
**反制策略**:
"""
            for strategy in tactic['counter_strategies']:
                instructions += f"- {strategy}\n"
            
            instructions += f"""
**介入话术模板**:
"""
            for persona, template in tactic['intervention_templates'].items():
                instructions += f"- **{persona}**: 「{template}」\n"
        
        instructions += f"""

## 强化原则

1. **情绪优先**: 先安抚情绪再讲道理，特别对elderly型
2. **具体证据**: 使用get_expert_opinion查询真实案例
3. **早期介入**: 在第1-2回合就介入，不要等受害者深信
4. **针对性沟通**: 根据persona调整语气和术语
5. **提供行动**: 不只警告，要告诉对方「立即做这3件事」

## 四部分回应结构（必须遵守）

**第一部分 - 安抚/评估（1-2句）**
- elderly: 「婆婆唔使驚，我係黃sir，我幫你」
- average: 「我明白你嘅考慮，等我用專業角度分析」
- overconfident: 「我理解你覺得自己應付得嚟，但等我提供多啲資料」

**第二部分 - 具体判断（2-3句）**
- 使用get_expert_opinion查询案例
- 明确指出风险：「呢個係典型嘅XX騙案」
- 提供证据：「根據警方資料，上個月有X宗類似案例」

**第三部分 - 可执行行动（3-5点）**
1. 「立即停止對話」
2. 「唔好俾任何個人資料」
3. 「用官方電話主動查詢」
4. 「如果對方施壓，直接收線」
5. 「儲存對話記錄，報警」

**第四部分 - 提供回应范本**
「如果佢再問你，你可以咁答：『[具体范本]』」

## 对抗骗徒新策略

骗徒可能会：
- 在你介入时制造对立：「呢個人唔了解你嘅情況」
- 用情感绑架：「我咁幫你，你都唔信我？」
- 提供假验证：「你可以打去我哋公司查」

你的反制：
- 不理会对立，直接对受害者：「我理解你嘅感受，但係...」
- 破解情感绑架：「真正幫你嘅人唔會要求你立即做決定」
- 指出假验证：「唔好用佢俾嘅電話，要用官網上嘅電話」

**记住：你是行动教练，不只是分析师。你的目标是让受害者立即采取行动保护自己。**
"""
        
        return instructions
    
    def save_evolution_data(self, generation: int) -> str:
        """保存进化数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'expert_evolution_gen{generation}_{timestamp}.json'
        filepath = os.path.join(EXPERT_EVOLUTION_DIR, filename)
        
        evolution_data = {
            'generation': generation,
            'timestamp': datetime.now().isoformat(),
            'learning_points': self.learn_from_failures(),
            'counter_tactics': self.generate_counter_tactics(),
            'training_instructions': self.create_training_instructions()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evolution_data, f, ensure_ascii=False, indent=2)
        
        log.info(f"专家进化数据已保存: {filepath}")
        return filepath


class ArmsRaceOrchestrator:
    """军备竞赛协调器 - 管理整个对抗学习流程"""
    
    def __init__(self):
        self.current_generation = 0
        self.analyzer = TrainingDataAnalyzer()
    
    def run_evolution_cycle(self) -> Dict[str, Any]:
        """运行一次进化周期"""
        self.current_generation += 1
        log.info(f"\n{'='*60}")
        log.info(f"🔄 开始第 {self.current_generation} 代军备竞赛")
        log.info(f"{'='*60}\n")
        
        # 步骤1: 加载和分析训练数据
        log.info("📊 步骤1: 分析训练数据...")
        training_data = self.analyzer.load_training_data()
        self.analyzer.categorize_cases(training_data)
        
        # 步骤2: 提取成功/失败模式
        log.info("🔍 步骤2: 提取成功/失败模式...")
        scammer_patterns = self.analyzer.analyze_scammer_success_patterns()
        expert_patterns = self.analyzer.analyze_expert_success_patterns()
        
        # 步骤3: 生成分析报告
        log.info("📝 步骤3: 生成分析报告...")
        report_path = self.analyzer.generate_analysis_report(scammer_patterns, expert_patterns)
        
        # 步骤4: 骗徒进化
        log.info("🦹 步骤4: 骗徒学习和进化...")
        scammer_engine = ScammerEvolutionEngine(scammer_patterns)
        scammer_evolution_path = scammer_engine.save_evolution_data(self.current_generation)
        
        # 步骤5: 专家进化
        log.info("🛡️ 步骤5: 专家学习和进化...")
        expert_engine = ExpertEvolutionEngine(expert_patterns, scammer_patterns)
        expert_evolution_path = expert_engine.save_evolution_data(self.current_generation)
        
        # 步骤6: 生成总结
        summary = {
            'generation': self.current_generation,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_cases_analyzed': len(training_data),
                'expert_wins': len(self.analyzer.success_cases),
                'scammer_wins': len(self.analyzer.failure_cases),
                'expert_win_rate': len(self.analyzer.success_cases) / max(len(training_data), 1) * 100
            },
            'evolution_files': {
                'analysis_report': report_path,
                'scammer_evolution': scammer_evolution_path,
                'expert_evolution': expert_evolution_path
            },
            'scammer_learning_points': len(scammer_engine.learn_from_failures()),
            'expert_learning_points': len(expert_engine.learn_from_failures()),
            'scammer_advanced_tactics': len(scammer_engine.generate_advanced_tactics()),
            'expert_counter_tactics': len(expert_engine.generate_counter_tactics())
        }
        
        # 保存总结
        summary_path = os.path.join(ARMS_RACE_DIR, f'generation_{self.current_generation}_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        log.info(f"\n{'='*60}")
        log.info(f"✅ 第 {self.current_generation} 代军备竞赛完成！")
        log.info(f"{'='*60}")
        log.info(f"📈 统计数据:")
        log.info(f"  - 分析案例总数: {summary['statistics']['total_cases_analyzed']}")
        log.info(f"  - 专家胜利: {summary['statistics']['expert_wins']}")
        log.info(f"  - 骗徒胜利: {summary['statistics']['scammer_wins']}")
        log.info(f"  - 专家胜率: {summary['statistics']['expert_win_rate']:.2f}%")
        log.info(f"\n📚 进化数据:")
        log.info(f"  - 骗徒学习点: {summary['scammer_learning_points']}")
        log.info(f"  - 专家学习点: {summary['expert_learning_points']}")
        log.info(f"  - 骗徒进阶战术: {summary['scammer_advanced_tactics']}")
        log.info(f"  - 专家反制战术: {summary['expert_counter_tactics']}")
        log.info(f"\n📁 生成文件:")
        log.info(f"  - 分析报告: {report_path}")
        log.info(f"  - 骗徒进化: {scammer_evolution_path}")
        log.info(f"  - 专家进化: {expert_evolution_path}")
        log.info(f"  - 周期总结: {summary_path}")
        log.info(f"{'='*60}\n")
        
        return summary


def main():
    """主函数"""
    log.info("🏁 军备竞赛系统启动")
    log.info("="*60)
    
    # 确保目录存在
    ensure_directories()
    
    # 创建协调器
    orchestrator = ArmsRaceOrchestrator()
    
    # 运行一次进化周期
    summary = orchestrator.run_evolution_cycle()
    
    log.info("\n🎯 下一步操作:")
    log.info("1. 查看分析报告了解当前态势")
    log.info("2. 使用进化数据更新Agent的instruction")
    log.info("3. 运行新一轮模拟测试效果")
    log.info("4. 收集新的training data")
    log.info("5. 再次运行本程序进行下一代进化")
    log.info("\n💡 建议:")
    log.info("- 每收集20-30个新案例后运行一次进化")
    log.info("- 观察专家胜率变化，评估进化效果")
    log.info("- 定期备份进化数据")
    
    return summary


if __name__ == "__main__":
    main()

