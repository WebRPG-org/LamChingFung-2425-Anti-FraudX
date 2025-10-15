"""
CrewAI team for deep analysis of multimedia content
"""
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json
from typing import Dict, List, Any

class AnalysisCrew:
    def __init__(self):
        # Initialize AI models
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        
        # Define specialized agents
        self.fraud_analyst = self._create_fraud_analyst()
        self.risk_assessor = self._create_risk_assessor()
        self.safety_advisor = self._create_safety_advisor()
        self.timeline_creator = self._create_timeline_creator()
    
    def _create_fraud_analyst(self) -> Agent:
        """Create fraud detection specialist agent"""
        return Agent(
            role="詐騙分析專家",
            goal="識別和分析多媒體內容中的詐騙風險指標",
            backstory="""你是一位經驗豐富的金融詐騙分析專家，專門識別各種詐騙手法和風險指標。
            你對香港的金融詐騙模式有深入了解，能夠從文字、語音、影像中識別可疑行為。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _create_risk_assessor(self) -> Agent:
        """Create risk assessment specialist agent"""
        return Agent(
            role="風險評估專家",
            goal="評估多媒體內容的風險等級和緊急程度",
            backstory="""你是一位專業的風險評估專家，能夠根據各種指標評估詐騙風險的嚴重程度。
            你了解不同類型詐騙的風險等級，能夠提供準確的風險評估。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _create_safety_advisor(self) -> Agent:
        """Create safety advisor agent"""
        return Agent(
            role="安全顧問",
            goal="提供具體的安全建議和防護措施",
            backstory="""你是一位專業的安全顧問，專門為長者提供防詐騙建議。
            你了解長者的特殊需求，能夠提供簡單易懂、實用的安全建議。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _create_timeline_creator(self) -> Agent:
        """Create timeline creation specialist agent"""
        return Agent(
            role="時間軸分析師",
            goal="創建詳細的事件時間軸和行為模式分析",
            backstory="""你是一位專業的時間軸分析師，能夠從多媒體內容中提取關鍵事件，
            並創建清晰的事件時間軸，幫助理解詐騙過程。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis function"""
        
        # Create analysis tasks
        fraud_analysis_task = Task(
            description=f"""
            請分析以下多媒體內容，識別潛在的詐騙風險指標：
            
            文字內容：{content_data.get('text', '')}
            音頻轉錄：{content_data.get('audio_transcription', '')}
            檢測到的物件：{content_data.get('objects', [])}
            檢測到的文字：{content_data.get('text_detected', [])}
            活動分析：{content_data.get('activities', [])}
            
            請提供：
            1. 識別到的詐騙風險指標
            2. 可疑行為模式
            3. 緊急程度評估
            """,
            agent=self.fraud_analyst,
            expected_output="詐騙風險分析報告"
        )
        
        risk_assessment_task = Task(
            description=f"""
            基於詐騙分析結果，評估整體風險等級：
            
            詐騙分析結果：{fraud_analysis_task}
            
            請提供：
            1. 風險等級（低/中/高/極高）
            2. 緊急程度（1-10分）
            3. 主要風險因素
            4. 建議的應對措施
            """,
            agent=self.risk_assessor,
            expected_output="風險評估報告"
        )
        
        safety_advice_task = Task(
            description=f"""
            基於風險評估，為長者提供具體的安全建議：
            
            風險評估：{risk_assessment_task}
            
            請提供：
            1. 立即行動建議
            2. 防護措施
            3. 求助管道
            4. 預防措施
            """,
            agent=self.safety_advisor,
            expected_output="安全建議清單"
        )
        
        timeline_task = Task(
            description=f"""
            創建詳細的事件時間軸：
            
            原始內容：{content_data}
            分析結果：{fraud_analysis_task}
            
            請提供：
            1. 事件時間軸
            2. 關鍵行為模式
            3. 可疑操作序列
            """,
            agent=self.timeline_creator,
            expected_output="事件時間軸"
        )
        
        # Create and run crew
        crew = Crew(
            agents=[
                self.fraud_analyst,
                self.risk_assessor,
                self.safety_advisor,
                self.timeline_creator
            ],
            tasks=[
                fraud_analysis_task,
                risk_assessment_task,
                safety_advice_task,
                timeline_task
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute analysis
        result = crew.kickoff()
        
        return {
            "fraud_analysis": fraud_analysis_task.output,
            "risk_assessment": risk_assessment_task.output,
            "safety_advice": safety_advice_task.output,
            "timeline": timeline_task.output,
            "overall_result": result
        }
    
    def generate_elder_friendly_report(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate elder-friendly analysis report"""
        
        elder_report = {
            "summary": self._create_simple_summary(analysis_result),
            "immediate_actions": self._extract_immediate_actions(analysis_result),
            "safety_tips": self._create_safety_tips(analysis_result),
            "contact_info": self._get_emergency_contacts(),
            "risk_level": self._determine_risk_level(analysis_result)
        }
        
        return elder_report
    
    def _create_simple_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Create simple summary for elders"""
        return f"""
        分析結果摘要：
        
        我們發現了 {analysis_result.get('risk_level', '未知')} 的風險等級。
        
        主要發現：
        - {analysis_result.get('fraud_analysis', '正在分析中...')}
        
        建議：
        - {analysis_result.get('safety_advice', '請保持警惕')}
        """
    
    def _extract_immediate_actions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Extract immediate actions for elders"""
        return [
            "立即停止任何可疑操作",
            "不要提供個人信息",
            "聯繫家人或朋友",
            "如有疑問，請撥打防詐騙熱線"
        ]
    
    def _create_safety_tips(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Create safety tips for elders"""
        return [
            "永遠不要相信緊急要求轉帳的訊息",
            "不要點擊可疑的連結",
            "定期檢查銀行帳戶",
            "遇到可疑情況時，先與家人商量"
        ]
    
    def _get_emergency_contacts(self) -> Dict[str, str]:
        """Get emergency contact information"""
        return {
            "防詐騙熱線": "18222",
            "警務處": "999",
            "消費者委員會": "2929 2222",
            "金管局": "2878 8196"
        }
    
    def _determine_risk_level(self, analysis_result: Dict[str, Any]) -> str:
        """Determine overall risk level"""
        # Simple risk level determination logic
        if "極高" in str(analysis_result.get('risk_assessment', '')):
            return "極高"
        elif "高" in str(analysis_result.get('risk_assessment', '')):
            return "高"
        elif "中" in str(analysis_result.get('risk_assessment', '')):
            return "中"
        else:
            return "低"

