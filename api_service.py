# api_service.py
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import time

# --- 應用程式定義 ---
app = FastAPI(title="AI Text Analysis API")

# --- 模擬 AI 分析數據庫 (實際部署時替換為 LLM/爬蟲邏輯) ---
MOCK_AI_DATABASE = {
    "2330.TW": {
        "emotion": "強烈看漲",
        "conclusion": "AI 需求爆發，法說會展望樂觀，長期技術領先優勢強勁。",
        "positive_news": ["Q3 財報超預期，AI 需求是主要動能。", "多家券商調高目標價。"],
        "negative_news": ["短期股價漲多，有技術性整理壓力。"]
    },
    "00878.TW": {
        "emotion": "中性偏看漲",
        "conclusion": "ETF 結構具備成長與防禦，基本面支撐趨勢向上。",
        "positive_news": ["AI + 金融雙動能。", "規模穩定成長，填息率穩定。"],
        "negative_news": ["需關注配息波動。"]
    },
    "0050.TW": {
        "emotion": "中性偏看漲",
        "conclusion": "核心資產優勢和台積電支撐，儘管短期有調節，長期仍具穩健成長動力。",
        "positive_news": ["規模朝兆元級 ETF 前進。", "台積電權重高，受惠 AI 浪潮。"],
        "negative_news": ["近期外資持續賣超。"]
    }
}

# --- 定義 API 響應格式 ---
class AIAnalysisResponse(BaseModel):
    ticker: str
    timestamp: str
    emotion: str
    conclusion: str
    positive_news: list[str]
    negative_news: list[str]

# --- API 端點 ---
@app.get("/api/analyze/{ticker}", response_model=AIAnalysisResponse)
async def get_ai_analysis(ticker: str):
    """根據股票代碼提供 AI 文本分析報告。"""
    ticker = ticker.upper()

    if ticker in MOCK_AI_DATABASE:
        data = MOCK_AI_DATABASE[ticker]
        return AIAnalysisResponse(
            ticker=ticker,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            emotion=data["emotion"],
            conclusion=data["conclusion"],
            positive_news=data["positive_news"],
            negative_news=data["negative_news"]
        )
    else:
        # 如果代碼不在，返回中性結果 (確保 Streamlit 不會報錯)
        return AIAnalysisResponse(
            ticker=ticker,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            emotion="中性",
            conclusion=f"AI 分析庫暫無 {ticker} 的文本數據，僅提供量化分析。",
            positive_news=[],
            negative_news=[]
        )
      pip install fastapi uvicorn pydantic requests
