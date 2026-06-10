
# ENTOD Executive Dashboard V2
# Drop-in replacement for medisales_app.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ENTOD Executive Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("Data.xlsb", engine="pyxlsb")
    if pd.api.types.is_numeric_dtype(df["Month"]):
        df["Month"] = pd.to_datetime(df["Month"].astype(int), unit="D", origin="1899-12-30")
    df["Month"] = pd.to_datetime(df["Month"])
    df["Month_Period"] = df["Month"].dt.to_period("M")
    return df

df = load_data()

st.markdown("# ENTOD Commercial Performance Dashboard")
st.caption("Executive Sales Intelligence Platform")

with st.sidebar:
    st.header("Filters")
    state = st.multiselect("State", sorted(df["State Name"].dropna().unique()))
    division = st.multiselect("Division", sorted(df["Division Name"].dropna().unique()))

if state:
    df = df[df["State Name"].isin(state)]
if division:
    df = df[df["Division Name"].isin(division)]

total_rev = df["Sales Amt"].sum()
total_qty = df["Sales Qty"].sum()

top_product = df.groupby("Product Name")["Sales Amt"].sum().idxmax()
top_state = df.groupby("State Name")["Sales Amt"].sum().idxmax()

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue", f"₹{total_rev:,.0f}")
c2.metric("Quantity", f"{total_qty:,.0f}")
c3.metric("Top Product", top_product)
c4.metric("Top State", top_state)

trend = df.groupby("Month_Period")["Sales Amt"].sum().reset_index()
trend["Month_Period"] = trend["Month_Period"].astype(str)

st.subheader("Revenue Trend")
st.plotly_chart(px.line(trend, x="Month_Period", y="Sales Amt"), use_container_width=True)

col1,col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Products")
    prod = df.groupby("Product Name")["Sales Amt"].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(prod, x="Sales Amt", y="Product Name", orientation="h"),
                    use_container_width=True)

with col2:
    st.subheader("Top 10 States")
    states = df.groupby("State Name")["Sales Amt"].sum().nlargest(10).reset_index()
    st.plotly_chart(px.bar(states, x="Sales Amt", y="State Name", orientation="h"),
                    use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Base CSV File", csv, "ENTOD_Sales_Data.csv", "text/csv")
