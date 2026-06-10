import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💊 MediSales India Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
.kpi-card {
    background: linear-gradient(135deg, #1e293b, #334155);
    border: 1px solid rgba(99,179,237,0.2); border-radius: 16px;
    padding: 20px 24px; text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(99,179,237,0.2); }
.kpi-icon  { font-size: 2rem; margin-bottom: 6px; }
.kpi-label { font-size: 0.75rem; font-weight: 700; color: #94a3b8;
             letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 4px; }
.kpi-value { font-size: 1.9rem; font-weight: 900; color: #e2e8f0; line-height: 1.1; }
.kpi-sub   { font-size: 0.72rem; color: #64748b; margin-top: 4px; }
.section-header {
    display: flex; align-items: center; gap: 10px;
    margin: 28px 0 12px 0; padding-bottom: 8px;
    border-bottom: 2px solid rgba(99,179,237,0.2);
}
.section-header span { font-size: 1.15rem; font-weight: 800; color: #e2e8f0; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a2744 0%, #0f172a 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.15);
}
h1, h2, h3 { color: #e2e8f0 !important; }
.stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING  —  reads Data.xlsb directly (11 MB, GitHub-safe ✅)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="⏳ Loading data…", ttl=3600)
def load_data() -> pd.DataFrame:
    import os

    # ── Primary: your binary Excel file ──────────────────────────────────────
    if os.path.exists("Data.xlsb"):
        df = pd.read_excel("Data.xlsb", engine="pyxlsb")
        # xlsb stores dates as Excel serial integers → convert to real dates
        if pd.api.types.is_integer_dtype(df["Month"]) or pd.api.types.is_float_dtype(df["Month"]):
            df["Month"] = pd.to_datetime(
                df["Month"].astype(int), unit="D", origin="1899-12-30"
            )

    # ── Fallback: plain xlsx ──────────────────────────────────────────────────
    elif os.path.exists("Data.xlsx") or os.path.exists("data_xlsx.xlsx"):
        path = "Data.xlsx" if os.path.exists("Data.xlsx") else "data_xlsx.xlsx"
        df = pd.read_excel(path, engine="openpyxl")
        df["Month"] = pd.to_datetime(df["Month"])

    # ── Fallback: pkl (old format) ────────────────────────────────────────────
    elif os.path.exists("data.pkl"):
        df = pd.read_pickle("data.pkl", compression="gzip")
        df["Month"] = pd.to_datetime(df["Month"])

    # ── Fallback: zip/csv ─────────────────────────────────────────────────────
    elif os.path.exists("data.zip"):
        import zipfile
        with zipfile.ZipFile("data.zip") as z:
            with z.open("data.csv") as f:
                df = pd.read_csv(f)
        df["Month"] = pd.to_datetime(df["Month"])

    else:
        return None

    df["Month"]        = pd.to_datetime(df["Month"])
    df["Month_Period"] = df["Month"].dt.to_period("M")
    df["Month_Label"]  = df["Month"].dt.strftime("%b %Y")
    return df


df_full = load_data()
if df_full is None:
    st.error(
        "❌ Could not find the data file. "
        "Make sure **Data.xlsb** is in the same folder as app.py and try again."
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — FILTERS
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 💊 MediSales India")
    st.markdown("---")
    st.markdown("### 🔎 Filter Data")

    all_states    = sorted(df_full["State Name"].dropna().unique())
    sel_states    = st.multiselect("🗺️ State",    all_states,    default=[], placeholder="All states")

    all_divisions = sorted(df_full["Division Name"].dropna().unique())
    sel_divisions = st.multiselect("🏢 Division", all_divisions, default=[], placeholder="All divisions")

    all_products  = sorted(df_full["Product Name"].dropna().unique())
    sel_products  = st.multiselect("💊 Product",  all_products,  default=[], placeholder="All products")

    st.markdown("#### 📅 Month Range")
    min_date = df_full["Month"].min().date()
    max_date = df_full["Month"].max().date()
    date_from, date_to = st.slider(
        "Select range",
        min_value=min_date, max_value=max_date,
        value=(min_date, max_date),
        format="MMM YYYY",
    )

    st.markdown("---")
    last_month = df_full["Month"].max().strftime("%b %Y")
    st.caption(f"📅 Data up to: **{last_month}**")
    st.caption("💡 Leave filters blank = include all.")


# ══════════════════════════════════════════════════════════════════════════════
# APPLY FILTERS
# ══════════════════════════════════════════════════════════════════════════════

df = df_full.copy()
if sel_states:    df = df[df["State Name"].isin(sel_states)]
if sel_divisions: df = df[df["Division Name"].isin(sel_divisions)]
if sel_products:  df = df[df["Product Name"].isin(sel_products)]
df = df[(df["Month"].dt.date >= date_from) & (df["Month"].dt.date <= date_to)]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    "<h1 style='text-align:center;font-size:2.4rem;font-weight:900;"
    "background:linear-gradient(90deg,#63b3ed,#9f7aea,#f687b3);-webkit-background-clip:text;"
    "-webkit-text-fill-color:transparent;margin-bottom:4px;'>"
    "💊 MediSales India Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#64748b;font-size:0.9rem;margin-top:0;'>"
    "Medicine Sales Analytics · April 2024 – May 2026</p>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("⚠️ No data matches your current filters. Please widen your selection.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════

total_amt     = df["Sales Amt"].sum()
total_qty     = df["Sales Qty"].sum()
active_states = df["State Name"].nunique()
div_rev       = df.groupby("Division Name")["Sales Amt"].sum()
top_division  = div_rev.idxmax()
top_div_pct   = (div_rev.max() / total_amt * 100) if total_amt else 0

def fmt_inr(val):
    if val >= 1e7:  return f"₹{val/1e7:.2f} Cr"
    if val >= 1e5:  return f"₹{val/1e5:.1f} L"
    return f"₹{val:,.0f}"

c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "💰", "Total Sales Amount", fmt_inr(total_amt),     "Filtered period"),
    (c2, "📦", "Total Sales Qty",    f"{total_qty:,.0f}",    "Units sold"),
    (c3, "🗺️", "Active States",      str(active_states),     "of 32 Indian states"),
    (c4, "🏆", "Top Division",       top_division,           f"{top_div_pct:.1f}% of revenue"),
]
for col, icon, label, value, sub in cards:
    fs = "1.9rem" if len(value) < 12 else "1.25rem"
    with col:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon'>{icon}</div>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value' style='font-size:{fs};'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

BG, PAPER, FONT, GRID = "rgba(0,0,0,0)", "rgba(0,0,0,0)", "#cbd5e1", "rgba(255,255,255,0.06)"
COLORS = ["#63b3ed","#9f7aea","#f687b3","#68d391","#fbd38d",
          "#fc8181","#4fd1c5","#f6ad55","#667eea","#ed64a6"]


# ══════════════════════════════════════════════════════════════════════════════
# SALES TREND
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>📈 Monthly Sales Trend</span></div>",
            unsafe_allow_html=True)

trend = df.groupby("Month", as_index=False)["Sales Amt"].sum().sort_values("Month")
trend["Month_Label"] = trend["Month"].dt.strftime("%b %Y")

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend["Month_Label"], y=trend["Sales Amt"],
    mode="lines+markers",
    line=dict(color="#63b3ed", width=3),
    marker=dict(size=7, color="#63b3ed", line=dict(color="#e2e8f0", width=1.5)),
    fill="tozeroy", fillcolor="rgba(99,179,237,0.12)",
    hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
))
fig_trend.update_layout(
    height=320, paper_bgcolor=PAPER, plot_bgcolor=BG,
    font=dict(color=FONT, family="Nunito"),
    xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=11)),
    yaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f", title="Sales Amount (₹)"),
    margin=dict(l=10, r=10, t=10, b=40), hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOP 10 PRODUCTS  &  SALES BY STATE
# ══════════════════════════════════════════════════════════════════════════════

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("<div class='section-header'><span>🥇 Top 10 Products by Revenue</span></div>",
                unsafe_allow_html=True)
    top10 = (df.groupby("Product Name", as_index=False)["Sales Amt"]
               .sum().nlargest(10, "Sales Amt").sort_values("Sales Amt"))
    fig_prod = go.Figure(go.Bar(
        x=top10["Sales Amt"], y=top10["Product Name"], orientation="h",
        marker=dict(color=top10["Sales Amt"], colorscale="Blues", showscale=False),
        text=[fmt_inr(v) for v in top10["Sales Amt"]],
        textposition="outside", textfont=dict(color=FONT, size=10),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
    ))
    fig_prod.update_layout(
        height=380, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f"),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        margin=dict(l=10, r=60, t=10, b=10),
    )
    st.plotly_chart(fig_prod, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'><span>🗺️ Sales by State</span></div>",
                unsafe_allow_html=True)
    state_sales = (df.groupby("State Name", as_index=False)["Sales Amt"]
                     .sum().sort_values("Sales Amt", ascending=False)
                     .head(15).sort_values("Sales Amt"))
    fig_state = go.Figure(go.Bar(
        x=state_sales["Sales Amt"], y=state_sales["State Name"], orientation="h",
        marker=dict(color=state_sales["Sales Amt"], colorscale="Purples", showscale=False),
        text=[fmt_inr(v) for v in state_sales["Sales Amt"]],
        textposition="outside", textfont=dict(color=FONT, size=10),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
    ))
    fig_state.update_layout(
        height=380, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f"),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        margin=dict(l=10, r=60, t=10, b=10),
    )
    st.plotly_chart(fig_state, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# DIVISION PIE  &  TOP HQs TABLE
# ══════════════════════════════════════════════════════════════════════════════

col_pie, col_hq = st.columns([1, 1])

with col_pie:
    st.markdown("<div class='section-header'><span>🏢 Division-wise Revenue Share</span></div>",
                unsafe_allow_html=True)
    div_data = df.groupby("Division Name", as_index=False)["Sales Amt"].sum()
    fig_pie = go.Figure(go.Pie(
        labels=div_data["Division Name"], values=div_data["Sales Amt"],
        hole=0.55,
        marker=dict(colors=COLORS, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent", textfont=dict(size=11, color=FONT),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig_pie.add_annotation(
        text=f"<b>{div_data.shape[0]}</b><br>Divisions",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=FONT, family="Nunito"),
    )
    fig_pie.update_layout(
        height=360, paper_bgcolor=PAPER,
        font=dict(color=FONT, family="Nunito"),
        margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_hq:
    st.markdown("<div class='section-header'><span>📍 Top Head Quarters / Territories</span></div>",
                unsafe_allow_html=True)
    hq_table = (
        df.groupby("Head Qtr", as_index=False)
          .agg(Revenue=("Sales Amt","sum"), Qty=("Sales Qty","sum"),
               Products=("Product Name","nunique"))
          .sort_values("Revenue", ascending=False).head(15).reset_index(drop=True)
    )
    hq_table.index += 1
    hq_table["Revenue"] = hq_table["Revenue"].apply(fmt_inr)
    hq_table["Qty"]     = hq_table["Qty"].apply(lambda x: f"{x:,}")
    hq_table.columns    = ["Head Quarter","Revenue","Qty Sold","# Products"]
    st.dataframe(hq_table, use_container_width=True, height=340)


# ══════════════════════════════════════════════════════════════════════════════
# RAW DATA PREVIEW
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🔍 Raw Data Preview (filtered)", expanded=False):
    st.caption(f"Showing first 1,000 rows of **{len(df):,}** filtered records.")
    preview = df.drop(columns=["Month_Period","Month_Label"], errors="ignore")
    st.dataframe(preview.head(1_000), use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;color:#334155;font-size:0.78rem;'>"
    "💊 MediSales India Dashboard · Built with Streamlit & Plotly</p>",
    unsafe_allow_html=True,
)
