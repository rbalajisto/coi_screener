import streamlit as st
import pandas as pd
from nselib import capital_market, derivatives
from datetime import datetime

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Combined OI Screener",
    page_icon="📊",
    layout="wide"
)

# -------------------- CONSTANTS (FROM YOUR CODE) --------------------
OptTp = 12
CompanyTicker = 7
OpenInt = 22
ChngOpenInt = 23

# -------------------- SIDEBAR --------------------
st.sidebar.title("⚙️ Screener Controls")

date_input = st.sidebar.text_input(
    "Bhavcopy Date (DD-MM-YYYY)",
    value=datetime.today().strftime("%d-%m-%Y")
)

cutoff = st.sidebar.slider(
    "OI Gainers Threshold (%)",
    min_value=5,
    max_value=50,
    value=10
)

btm = st.sidebar.slider(
    "OI Losers Threshold (%)",
    min_value=-50,
    max_value=-1,
    value=-5
)

run = st.sidebar.button("🚀 Run Screener")

# -------------------- HEADER --------------------
st.title("📊 Combined Open Interest Screener")
st.caption("Identifies stocks with significant combined OI build-up or unwinding")

st.divider()

# -------------------- MAIN LOGIC --------------------
if run:
    try:
        with st.spinner("Fetching F&O symbols..."):
            stoListData = capital_market.fno_equity_list()
            stoList = stoListData["symbol"].tolist()

        with st.spinner("Fetching Bhavcopy data..."):
            data = derivatives.fno_bhav_copy(date_input)

        # Initialize containers
        finalList = [[sym, 0, 0, 0, 0] for sym in stoList]
        OIWinners = []

        # Combined OI calculation
        for i in range(data.shape[0]):
            if data.iloc[i, OptTp] not in ["PE", "CE"]:
                for company in finalList:
                    if data.iloc[i, CompanyTicker] == company[0]:
                        company[1] += data.iloc[i, OpenInt]
                        company[2] += data.iloc[i, ChngOpenInt]

        # % OI Change
        for company in finalList:
            company[3] = company[1] - company[2]
            try:
                company[4] = (company[2] / company[3]) * 100
            except:
                company[4] = 0

            if company[4] >= cutoff or company[4] <= btm:
                OIWinners.append([date_input, company[0], company[4]])

        # DataFrames
        df = pd.DataFrame(
            finalList,
            columns=[
                "Symbol",
                "Combined OI",
                "Combined Change in OI",
                "Previous Day OI",
                "% Change in OI"
            ]
        ).sort_values("% Change in OI", ascending=False)

        winners_df = pd.DataFrame(
            OIWinners,
            columns=["Date", "Symbol", "% Change in OI"]
        )

        # -------------------- METRICS --------------------
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Stocks", len(df))
        col2.metric("OI Gainers", (df["% Change in OI"] >= cutoff).sum())
        col3.metric("OI Losers", (df["% Change in OI"] <= btm).sum())

        st.divider()

        # -------------------- TABLES --------------------
        st.subheader("📈 Combined OI Screener Results")
        st.dataframe(df, use_container_width=True, height=450)

        st.subheader("🏆 High-Conviction OI Movers")
        st.dataframe(winners_df, use_container_width=True)

        # -------------------- DOWNLOAD --------------------
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇️ Download Full OI Data",
                data=df.to_excel(index=False),
                file_name=f"OI_Data_{date_input}.xlsx"
            )

        with col2:
            st.download_button(
                "⬇️ Download OI Winners",
                data=winners_df.to_excel(index=False),
                file_name=f"OI_Winners_{date_input}.xlsx"
            )

    except Exception as e:
        st.error("⚠️ Error fetching data. Check date or NSE availability.")
        st.exception(e)

else:
    st.info("👈 Set parameters and click **Run Screener**")
