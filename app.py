# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import requests
import numpy as np

# --- 配置 FastAPI 服務地址 (必須與 Step 3.1 啟動的端口一致) ---
API_BASE_URL = "http://127.0.0.1:8000" 

# --- 數據分析與 API 呼叫 ---

@st.cache_data(ttl=3600) # 緩存數據，避免頻繁呼叫
def fetch_and_analyze(ticker, days=365):
    """抓取股價數據並進行基礎清洗與量化分析。"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            return None, "無法獲取股價數據。"
    except Exception:
        return None, "數據抓取失敗，請檢查代碼或網路。"
    
    # 股價處理與均線計算
    df = df.reset_index().rename(columns={'Close': 'Current_Price'})
    df['MA_Short'] = df['Current_Price'].rolling(window=5).mean()
    df['MA_Long'] = df['Current_Price'].rolling(window=20).mean()
    
    # 量化趨勢判斷
    quant_trend = "N/A"
    quant_desc = "數據不足，無法計算。"
    analyzed_df = df.dropna()
    if not analyzed_df.empty:
        latest_short_ma = analyzed_df['MA_Short'].iloc[-1]
        latest_long_ma = analyzed_df['MA_Long'].iloc[-1]
        quant_trend = "看漲" if latest_short_ma > latest_long_ma else "看跌/盤整"
        quant_desc = f"短期 (5日) vs 長期 (20日) 均線趨勢。"
        
    return df, quant_trend, quant_desc

def fetch_ai_analysis(ticker):
    """呼叫 FastAPI 服務獲取 AI 文本分析結果。"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/analyze/{ticker}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ **API 連接失敗！** 請確保 **FastAPI 服務 (api_service.py)** 已經運行。")
        return None
    except Exception:
        st.error("❌ AI 文本分析服務錯誤。")
        return None

# --- Streamlit UI 核心 ---

def main():
    st.set_page_config(page_title="小寶 AI 股市分析工具", layout="wide")
    st.title("🤖 小寶 AI 股市分析工具 (全自動化版)")
    st.markdown("---")
    
    # 頁面狀態管理 (用於實現「回上一頁」/重設)
    if 'page' not in st.session_state:
        st.session_state.page = 'input'
        st.session_state.ticker = '2330.TW'

    # 輸入頁面
    if st.session_state.page == 'input':
        st.info(f"✅ **系統要求:** 請確保後端 API 服務已在 {API_BASE_URL} 運行。")
        st.session_state.ticker = st.text_input("1️⃣ 輸入股票代碼 (例: 2330.TW, 00878.TW)", 
                                                st.session_state.ticker).upper()
        
        if st.button("🔍 生成自動化分析報告", type="primary"):
            st.session_state.page = 'report'
            st.rerun()

    # 報告頁面
    elif st.session_state.page == 'report':
        ticker = st.session_state.ticker
        
        # 運行分析
        df, quant_trend, quant_desc = fetch_and_analyze(ticker)
        ai_analysis_result = fetch_ai_analysis(ticker)

        if df is None or ai_analysis_result is None:
            # 錯誤或 API 連接失敗時的回上一頁按鈕
            if st.button("⬅️ 回上一頁 / 重新輸入"):
                st.session_state.page = 'input'
                st.rerun()
            return

        # --- 成功顯示報告 ---
        
        stock_name = ai_analysis_result['ticker'].replace(".TW", "")
        latest_info = {'price': df['Current_Price'].iloc[-1], 'date': df['Date'].iloc[-1].strftime('%Y-%m-%d')}
        
        st.header(f"📊 {ticker} {stock_name} 最終分析報告")
        st.caption(f"發布時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST")

        # 趨勢總結
        col_price, col_date, col_trend = st.columns(3)
        with col_price:
            st.metric(label="最新收盤價", value=f"NT$ {latest_info['price']:,.2f}")
        with col_date:
            st.metric(label="最新交易日", value=latest_info['date'])
        with col_trend:
            st.markdown(f"**⚡️ 綜合結論：**", unsafe_allow_html=True)
            st.markdown(f"## {ai_analysis_result['emotion']}")

        st.markdown("---")
        
        # 報告表格
        st.subheader("趨勢判斷與分析")
        report_table = pd.DataFrame({
            '分析類別': ['量化分析', 'AI 文本分析', '綜合結論'],
            '趨勢': [quant_trend, ai_analysis_result['emotion'], ai_analysis_result['emotion']],
            '簡要說明': [quant_desc, ai_analysis_result['conclusion'], ai_analysis_result['conclusion']]
        })
        st.table(report_table.set_index('分析類別'))
        
        # 新聞摘要
        st.subheader("📰 即時新聞摘要 (AI 情感分析)")
        st.success("**✅ 正面/利多消息：**")
        for item in ai_analysis_result['positive_news']:
            st.markdown(f"- {item}")
        st.error("**🔴 負面/需注意消息：**")
        for item in ai_analysis_result['negative_news']:
            st.markdown(f"- {item}")
        
        st.markdown("---")
        
        # 互動圖表
        st.subheader("股價與均線走勢圖")
        df_plot = df.dropna()
        fig = px.line(df_plot, x='Date', y=['Current_Price', 'MA_Short', 'MA_Long'])
        st.plotly_chart(fig, use_container_width=True)

        # 您要求的控制按鈕
        if st.button("⬅️ 回上一頁 / 重新輸入", type="secondary"):
            st.session_state.page = 'input'
            st.rerun()


if __name__ == "__main__":
    # 準備 Streamlit 依賴
    # pip install streamlit pandas yfinance plotly requests
    main()

pip install streamlit pandas yfinance plotly requests
