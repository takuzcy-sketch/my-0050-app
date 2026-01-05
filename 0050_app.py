import streamlit as st
import requests
import pandas as pd
import urllib3

# 關閉 SSL 警告訊息（因為我們會手動忽略憑證檢查）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 網頁基本設定
st.set_page_config(page_title="0050 期貨槓桿監控", layout="centered")
st.title("📊 0050 期貨槓桿即時監控")

# 2. 多重抓價邏輯 (證交所 + FinMind 備援)
@st.cache_data(ttl=300)
def get_realtime_price():
    # 方案 A：證交所 API (加入 verify=False 解決你的 SSL 錯誤)
    try:
        url_twse = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&stockNo=0050"
        res = requests.get(url_twse, timeout=10, verify=False)
        data = res.json()
        if data.get('data'):
            return float(data['data'][-1][1])
    except:
        pass

    # 方案 B：FinMind API (免費且穩定的第三方來源)
    try:
        url_fm = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=0050"
        res = requests.get(url_fm, timeout=10)
        data = res.json()
        if data.get('data'):
            return float(data['data'][-1]['close'])
    except:
        pass
    
    return None

market_price = get_realtime_price()

# 3. 持倉參數輸入
st.subheader("1. 持倉參數")
col1, col2 = st.columns(2)

with col1:
    # 這裡的預設價格改為目前 0050 的大約市價 190-200 之間
    price_input = st.number_input(
        "當前 0050 股價 (試算用)", 
        value=float(market_price) if market_price else 198.0, 
        step=0.1
    )
    contracts = st.number_input("持有口數", value=2, min_value=1, step=1)

with col2:
    balance = st.number_input("帳戶總餘額 (NT$)", value=500000, step=10000)
    spec = st.radio("合約規格", ["標準型 (10,000股)", "小型 (1,000股)"], horizontal=True)

# 4. 計算槓桿
multiplier = 10000 if "標準型" in spec else 1000
total_value = price_input * multiplier * contracts
leverage = total_value / balance if balance > 0 else 0
risk_buffer = (1 / leverage) * 100 if leverage > 0 else 0

# 5. 顯示監控結果
st.divider()
st.subheader("2. 監控結果")

# 根據你的投資風格（35歲、200萬資金、喜歡2.5倍槓桿）設定的警示燈
if leverage > 3.5:
    st.error(f"⚠️ 當前槓桿：{leverage:.2f} 倍 (風險極高)")
elif leverage > 2.5:
    st.warning(f"🟡 當前槓桿：{leverage:.2f} 倍 (接近設定上限)")
else:
    st.success(f"🟢 當前槓桿：{leverage:.2f} 倍 (穩健區間)")

c1, c2 = st.columns(2)
c1.metric("控制資產總額", f"NT$ {total_value:,.0f}")
c2.metric("耐震度 (跌多少賠光)", f"{risk_buffer:.1f}%")

# 6. 市場即時報價顯示
st.divider()
if market_price:
    st.info(f"💡 目前市場參考報價：${market_price}")
else:
    st.error("❌ 無法自動抓取價格。請手動在上方輸入目前股價。")

if st.button("🔄 重新整理價格"):
    st.cache_data.clear()
    st.rerun()