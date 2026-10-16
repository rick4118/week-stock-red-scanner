with open('app.py', 'w', encoding='utf-8') as f:
    f.write('''import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 網頁基本設定
st.set_page_config(page_title="周K MACD 篩選器", layout="wide")

# ==========================================
# 密碼驗證功能
# ==========================================
CORRECT_PASSWORD = "592888"  # 預設密碼設定為 592888

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == CORRECT_PASSWORD:
        st.session_state["authenticated"] = True
        st.session_state["password_error"] = False
    else:
        st.session_state["authenticated"] = False
        st.session_state["password_error"] = True

# 若未驗證成功，顯示密碼登入畫面
if not st.session_state["authenticated"]:
    st.title("🔐 系統登入")
    st.text_input(
        "請輸入密碼以解鎖篩選器：", 
        type="password", 
        key="password_input", 
        on_change=check_password
    )
    if st.session_state.get("password_error", False):
        st.error("❌ 密碼錯誤，請重新輸入！")
    st.stop()  # 中斷後續程式執行

# ==========================================
# 核心計算與篩選邏輯
# ==========================================

def compute_macd(df, fast=12, slow=26, signal=9):
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']
    df['MACD'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['OSC'] = df['DIF'] - df['MACD']
    return df

def scan_weekly_stocks_by_specific_date(ticker_list, target_date):
    result = []
    target_dt = pd.Timestamp(target_date)
    target_year_week = target_dt.to_period(\'W\')

    start_date = (target_dt - pd.Timedelta(days=365*2)).strftime(\'%Y-%m-%d\')
    end_date = (target_dt + pd.Timedelta(days=14)).strftime(\'%Y-%m-%d\')

    for ticker in ticker_list:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, interval="1wk", auto_adjust=False, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna(subset=["Close"])
            if len(df) < 35:
                continue

            df = compute_macd(df)
            df_periods = df.index.to_period(\'W\')
            valid_mask = df_periods <= target_year_week

            if not valid_mask.any():
                continue

            target_idx = df[valid_mask].index[-1]
            idx_loc = df.index.get_loc(target_idx)

            if idx_loc < 2:
                continue

            recent = df.iloc[idx_loc-2 : idx_loc+1].copy()
            osc_val = recent[\'OSC\'].values.flatten()

            # 紅柱增條件
            pure_red_expand = (osc_val[-2] > 0) and (osc_val[-1] > 0) and (osc_val[-1] > osc_val[-2])

            if pure_red_expand:
                result.append(ticker)

        except Exception:
            pass
    return result

# ==========================================
# 主介面排版
# ==========================================
st.title("📈 一體化周K MACD 紅柱增篩選器")

with st.sidebar:
    st.success("🔓 已驗證成功")
    if st.button("安全登出"):
        st.session_state["authenticated"] = False
        st.rerun()

default_tickers = "0056.TW, 1301.TW, 1303.TW, 1308.TW, 1312A.TW, 1316.TW, 1319.TW, 1326.TW, 1336.TWO, 1416.TW, 1440.TW, 1504.TW, 1515.TW, 1519.TW, 1558.TW"

col1, col2 = st.columns([2, 1])

with col1:
    tickers_input = st.text_area(
        "請輸入股票代號（支援空格、逗號、換行分隔）：", 
        value=default_tickers,
        height=150
    )

date_picker = st.date_input("選擇基準日期：", value=datetime.today())

run_button = st.button("🚀 開始篩選", type="primary")

if run_button:
    raw_input = tickers_input
    for char in [\',\', \';\', \'\\n\', \'\\t\', \'，\', \'；\']:
        raw_input = raw_input.replace(char, \' \')

    cleaned_tickers = [t.strip() for t in raw_input.split(\' \') if t.strip()]

    if not cleaned_tickers:
        st.error("❌ 請輸入至少一個股票代號！")
    else:
        formatted_tickers = [f"{t}.TW" if "." not in t else t for t in cleaned_tickers]
        target_date_str = date_picker.strftime(\'%Y-%m-%d\')

        with st.spinner("⏳ 正在下載最新資料並進行篩選，請稍候..."):
            results = scan_weekly_stocks_by_specific_date(formatted_tickers, target_date_str)

        st.success("🎉 篩選完成！")
        
        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("基準日期 (對應周K)", target_date_str)
        metric_col2.metric("總掃描檔數", f"{len(formatted_tickers)} 檔")

        st.markdown("--- ")
        if results:
            st.subheader(f"✅ 符合「周K MACD 紅柱增」的股票 ({len(results)} 檔)：")
            st.code(", ".join(results), language="text")
            st.info("📋 提示：您可以直接複製上方代號列，貼至您的自選股中。")
        else:
            st.warning("⚠️ 查無符合條件的股票。")
''')
print("Streamlit 檔案 app.py 已成功建立，預設密碼為 592888！")
