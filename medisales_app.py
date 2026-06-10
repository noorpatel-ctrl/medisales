import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ENTOD Sales Insight",
    page_icon="https://img1.wsimg.com/isteam/ip/a42bf746-f9eb-4662-bf91-1cf8282331d5/blob-bf39cdb.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── ENTOD Brand Colors ─────────────────────────────────────────────────────────
# Primary: #f50f12 (ENTOD Red)
# Dark BG: #0d0d0d / #1a0000
# Accent:  #ff4444, #cc0000
# Text:    #f0f0f0, #aaaaaa

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }

/* ── Page background ── */
.stApp {
    background: linear-gradient(160deg, #0d0d0d 0%, #1a0000 50%, #0d0d0d 100%);
}

/* ── Scrolling ticker ── */
.ticker-wrap {
    width: 100%; overflow: hidden;
    background: linear-gradient(90deg, #f50f12, #cc0000);
    padding: 8px 0; margin-bottom: 8px;
    border-radius: 8px;
}
.ticker {
    display: inline-block;
    white-space: nowrap;
    animation: ticker-scroll 20s linear infinite;
    color: #fff; font-weight: 700; font-size: 0.9rem; letter-spacing: 0.05em;
}
@keyframes ticker-scroll {
    0%   { transform: translateX(100vw); }
    100% { transform: translateX(-100%); }
}

/* ── KPI cards ── */
.kpi-card {
    background: linear-gradient(135deg, #1a0000 0%, #2d0000 100%);
    border: 1px solid rgba(245,15,18,0.35);
    border-radius: 16px; padding: 18px 20px; text-align: center;
    box-shadow: 0 4px 20px rgba(245,15,18,0.15);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(245,15,18,0.3);
    border-color: rgba(245,15,18,0.6);
}
.kpi-icon  { font-size: 1.8rem; margin-bottom: 5px; }
.kpi-label { font-size: 0.7rem; font-weight: 700; color: #888;
             letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 4px; }
.kpi-value { font-size: 1.75rem; font-weight: 900; color: #f0f0f0; line-height: 1.1; }
.kpi-sub   { font-size: 0.7rem; color: #f50f12; margin-top: 4px; font-weight: 600; }

/* ── Section headers ── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    margin: 24px 0 10px 0; padding-bottom: 8px;
    border-bottom: 2px solid rgba(245,15,18,0.4);
}
.section-header span {
    font-size: 1.1rem; font-weight: 800; color: #f0f0f0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0000 0%, #0d0d0d 100%) !important;
    border-right: 1px solid rgba(245,15,18,0.2);
}

/* ── General text ── */
h1, h2, h3 { color: #f0f0f0 !important; }
.stDataFrame { border-radius: 12px; overflow: hidden; }
p, label, .stMarkdown { color: #ccc; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="⏳ Loading ENTOD Sales Data…", ttl=3600)
def load_data() -> pd.DataFrame:
    import os, zipfile

    if os.path.exists("Data.xlsb"):
        df = pd.read_excel("Data.xlsb", engine="pyxlsb")
        if pd.api.types.is_integer_dtype(df["Month"]) or pd.api.types.is_float_dtype(df["Month"]):
            df["Month"] = pd.to_datetime(df["Month"].astype(int), unit="D", origin="1899-12-30")
    elif os.path.exists("Data.xlsx") or os.path.exists("data_xlsx.xlsx"):
        path = "Data.xlsx" if os.path.exists("Data.xlsx") else "data_xlsx.xlsx"
        df = pd.read_excel(path, engine="openpyxl")
    elif os.path.exists("data.pkl"):
        df = pd.read_pickle("data.pkl", compression="gzip")
    elif os.path.exists("data.zip"):
        with zipfile.ZipFile("data.zip") as z:
            with z.open("data.csv") as f:
                df = pd.read_csv(f)
    else:
        return None

    df["Month"]        = pd.to_datetime(df["Month"])
    df["Month_Label"]  = df["Month"].dt.strftime("%b %Y")
    df["Month_Period"] = df["Month"].dt.to_period("M")
    return df


df_full = load_data()
if df_full is None:
    st.error("❌ Could not find the data file. Make sure Data.xlsb is in the same folder as this app.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — FILTERS
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Logo + title
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 5px 0;'>
        <img src='https://img1.wsimg.com/isteam/ip/a42bf746-f9eb-4662-bf91-1cf8282331d5/blob-bf39cdb.png'
             style='height:60px; object-fit:contain;'
             onerror="this.style.display='none'"/>
        <div style='color:#f50f12; font-weight:900; font-size:1.1rem; margin-top:6px;'>
            ENTOD Sales Insight
        </div>
        <div style='color:#666; font-size:0.7rem;'>Sales Analytics Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔎 Filters")

    # ── Month picker (individual months, not range) ──────────────────────────
    all_months_sorted = sorted(df_full["Month"].dt.to_period("M").unique())
    all_month_labels  = [str(m) for m in all_months_sorted]
    # convert to display labels like "Apr 2024"
    month_display     = [pd.Period(m).strftime("%b %Y") for m in all_month_labels]
    month_map         = dict(zip(month_display, all_month_labels))

    sel_months_display = st.multiselect(
        "📅 Month", month_display,
        default=[], placeholder="All months"
    )

    st.markdown("---")

    all_states    = sorted(df_full["State Name"].dropna().unique())
    sel_states    = st.multiselect("🗺️ State",    all_states,    default=[], placeholder="All states")

    all_divisions = sorted(df_full["Division Name"].dropna().unique())
    sel_divisions = st.multiselect("🏢 Division", all_divisions, default=[], placeholder="All divisions")

    all_products  = sorted(df_full["Product Name"].dropna().unique())
    sel_products  = st.multiselect("💊 Product",  all_products,  default=[], placeholder="All products")

    st.markdown("---")
    last_month = df_full["Month"].max().strftime("%b %Y")
    st.caption(f"📅 Data up to: **{last_month}**")
    st.caption("💡 Leave filters blank = include all.")


# ══════════════════════════════════════════════════════════════════════════════
# APPLY FILTERS
# ══════════════════════════════════════════════════════════════════════════════

df = df_full.copy()

if sel_months_display:
    sel_periods = [pd.Period(month_map[m]) for m in sel_months_display]
    df = df[df["Month_Period"].isin(sel_periods)]

if sel_states:    df = df[df["State Name"].isin(sel_states)]
if sel_divisions: df = df[df["Division Name"].isin(sel_divisions)]
if sel_products:  df = df[df["Product Name"].isin(sel_products)]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER — Logo + Title + Ticker
# ══════════════════════════════════════════════════════════════════════════════

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("""
    <div style='padding-top:8px;'>
        <img src='https://img1.wsimg.com/isteam/ip/a42bf746-f9eb-4662-bf91-1cf8282331d5/blob-bf39cdb.png'
             style='height:64px; object-fit:contain;'
             onerror="this.style.display='none'"/>
    </div>
    """, unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <div style='padding-top:4px;'>
        <h1 style='margin:0; font-size:2.2rem; font-weight:900;
            background: linear-gradient(90deg, #f50f12, #ff6666, #f50f12);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            line-height:1.1;'>
            ENTOD Sales Insight
        </h1>
        <p style='margin:2px 0 0 2px; color:#666; font-size:0.82rem;'>
            Ophthalmic · ENT · Dermatology &nbsp;|&nbsp; India Sales Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Scrolling ticker ──────────────────────────────────────────────────────────
st.markdown("""
<div class='ticker-wrap'>
    <span class='ticker'>
        ⚠️&nbsp;&nbsp;This Dashboard Is Daily Refreshed at 10 AM and 5 PM &nbsp;&nbsp;|&nbsp;&nbsp;
        ⚠️&nbsp;&nbsp;This Dashboard Is Daily Refreshed at 10 AM and 5 PM &nbsp;&nbsp;|&nbsp;&nbsp;
        ⚠️&nbsp;&nbsp;This Dashboard Is Daily Refreshed at 10 AM and 5 PM &nbsp;&nbsp;|&nbsp;&nbsp;
        ⚠️&nbsp;&nbsp;This Dashboard Is Daily Refreshed at 10 AM and 5 PM &nbsp;&nbsp;|&nbsp;&nbsp;
        ⚠️&nbsp;&nbsp;This Dashboard Is Daily Refreshed at 10 AM and 5 PM &nbsp;&nbsp;
    </span>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ No data matches your current filters. Please widen your selection.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════

def fmt_inr(val):
    if val >= 1e7:  return f"₹{val/1e7:.2f} Cr"
    if val >= 1e5:  return f"₹{val/1e5:.1f} L"
    return f"₹{val:,.0f}"

RED    = "#f50f12"
RED2   = "#ff4444"
BG     = "rgba(0,0,0,0)"
PAPER  = "rgba(0,0,0,0)"
FONT   = "#cccccc"
GRID   = "rgba(255,255,255,0.05)"
COLORS = [RED,"#ff6b6b","#ff9999","#ffcccc",
          "#cc0000","#990000","#ff3333","#ff8080","#ffaaaa","#ffe0e0"]


# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS  (6 manager-focused KPIs)
# ══════════════════════════════════════════════════════════════════════════════

total_amt    = df["Sales Amt"].sum()
total_qty    = df["Sales Qty"].sum()
num_products = df["Product Name"].nunique()
num_hqs      = df["Head Qtr"].nunique()

# Month-over-Month growth (last 2 months in filtered data)
monthly_rev = df.groupby("Month_Period")["Sales Amt"].sum().sort_index()
if len(monthly_rev) >= 2:
    last_val  = monthly_rev.iloc[-1]
    prev_val  = monthly_rev.iloc[-2]
    mom_growth = ((last_val - prev_val) / prev_val * 100) if prev_val else 0
    mom_str    = f"{'▲' if mom_growth >= 0 else '▼'} {abs(mom_growth):.1f}%"
    mom_color  = "#00e676" if mom_growth >= 0 else "#ff4444"
else:
    mom_str   = "N/A"
    mom_color = "#888"

# Avg Sales per HQ
avg_per_hq = total_amt / num_hqs if num_hqs else 0

st.markdown("<div class='section-header'><span>📊 Key Performance Indicators</span></div>",
            unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, "💰", "Total Revenue",      fmt_inr(total_amt),         "Filtered period"),
    (c2, "📦", "Total Units Sold",   f"{total_qty:,.0f}",         "Sales Qty"),
    (c3, "💊", "Active Products",    f"{num_products}",           "Unique SKUs"),
    (c4, "📍", "Active Territories", f"{num_hqs}",                "Head Quarters"),
    (c5, "📈", "MoM Growth",         mom_str,                     "vs previous month"),
    (c6, "🏙️", "Avg Rev / HQ",       fmt_inr(avg_per_hq),         "Per territory"),
]
for col, icon, label, value, sub in kpis:
    fs   = "1.7rem" if len(str(value)) < 10 else "1.1rem"
    vcol = mom_color if label == "MoM Growth" else "#f0f0f0"
    with col:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-icon'>{icon}</div>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value' style='font-size:{fs}; color:{vcol};'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — Sales Trend  +  MoM Growth
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>📈 Trend Analysis (Monthly)</span></div>",
            unsafe_allow_html=True)

trend = df.groupby("Month_Period", as_index=False)["Sales Amt"].sum().sort_values("Month_Period")
trend["Label"] = trend["Month_Period"].apply(lambda p: pd.Period(p).strftime("%b %Y"))
trend["MoM"]   = trend["Sales Amt"].pct_change() * 100

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Sales Trend — Revenue Over Time (Monthly)</div>",
                unsafe_allow_html=True)
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend["Label"], y=trend["Sales Amt"],
        mode="lines+markers",
        line=dict(color=RED, width=2.5),
        marker=dict(size=6, color=RED, line=dict(color="#fff", width=1)),
        fill="tozeroy", fillcolor="rgba(245,15,18,0.08)",
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    fig_trend.update_layout(
        height=280, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f"),
        margin=dict(l=10, r=10, t=10, b=40), hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_t2:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Month-over-Month Growth %</div>",
                unsafe_allow_html=True)
    colors_mom = [RED if v < 0 else "#00c853" for v in trend["MoM"].fillna(0)]
    fig_mom = go.Figure(go.Bar(
        x=trend["Label"], y=trend["MoM"],
        marker_color=colors_mom,
        text=trend["MoM"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else ""),
        textposition="outside", textfont=dict(size=9, color=FONT),
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig_mom.update_layout(
        height=280, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True,
                   zerolinecolor="rgba(255,255,255,0.2)"),
        margin=dict(l=10, r=10, t=20, b=40),
    )
    st.plotly_chart(fig_mom, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Top 10 Products  +  Sales by State
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>🏆 Product & State Performance</span></div>",
            unsafe_allow_html=True)

col_p, col_s = st.columns(2)

with col_p:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Top 10 Products by Revenue</div>",
                unsafe_allow_html=True)
    top10 = (df.groupby("Product Name", as_index=False)["Sales Amt"]
               .sum().nlargest(10, "Sales Amt").sort_values("Sales Amt"))
    fig_prod = go.Figure(go.Bar(
        x=top10["Sales Amt"], y=top10["Product Name"], orientation="h",
        marker=dict(color=top10["Sales Amt"],
                    colorscale=[[0,"#4a0000"],[0.5,"#cc0000"],[1,RED]],
                    showscale=False),
        text=[fmt_inr(v) for v in top10["Sales Amt"]],
        textposition="outside", textfont=dict(color=FONT, size=10),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
    ))
    fig_prod.update_layout(
        height=360, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=True, gridcolor=GRID),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        margin=dict(l=10, r=70, t=10, b=10),
    )
    st.plotly_chart(fig_prod, use_container_width=True)

with col_s:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Top 15 States by Revenue</div>",
                unsafe_allow_html=True)
    state_rev = (df.groupby("State Name", as_index=False)["Sales Amt"]
                   .sum().nlargest(15, "Sales Amt").sort_values("Sales Amt"))
    fig_state = go.Figure(go.Bar(
        x=state_rev["Sales Amt"], y=state_rev["State Name"], orientation="h",
        marker=dict(color=state_rev["Sales Amt"],
                    colorscale=[[0,"#2d0000"],[0.5,"#990000"],[1,"#ff4444"]],
                    showscale=False),
        text=[fmt_inr(v) for v in state_rev["Sales Amt"]],
        textposition="outside", textfont=dict(color=FONT, size=10),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
    ))
    fig_state.update_layout(
        height=360, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=True, gridcolor=GRID),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        margin=dict(l=10, r=70, t=10, b=10),
    )
    st.plotly_chart(fig_state, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Top 10 HQ by Sales Qty  +  Division Donut
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>📍 Territory & Division Breakdown</span></div>",
            unsafe_allow_html=True)

col_hq, col_div = st.columns(2)

with col_hq:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Top 10 Head Qtrs by Sales Qty (Monthly Avg)</div>",
                unsafe_allow_html=True)
    num_months = df["Month_Period"].nunique() or 1
    hq_qty = (df.groupby("Head Qtr", as_index=False)["Sales Qty"]
                .sum().nlargest(10, "Sales Qty").sort_values("Sales Qty"))
    hq_qty["Avg Qty (L)"] = hq_qty["Sales Qty"] / num_months / 1e5

    fig_hq = go.Figure(go.Bar(
        x=hq_qty["Head Qtr"], y=hq_qty["Avg Qty (L)"],
        marker=dict(color=hq_qty["Avg Qty (L)"],
                    colorscale=[[0,"#4a0000"],[0.5,RED],[1,"#ff6666"]],
                    showscale=True,
                    colorbar=dict(title="Sales Qty<br>(Lacs)", thickness=12,
                                  tickfont=dict(color=FONT, size=9),
                                  titlefont=dict(color=FONT, size=9))),
        text=hq_qty["Avg Qty (L)"].apply(lambda x: f"{x:.2f}"),
        textposition="outside", textfont=dict(size=9, color=FONT),
        hovertemplate="<b>%{x}</b><br>%{y:.2f} Lacs<extra></extra>",
    ))
    fig_hq.update_layout(
        height=340, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=GRID, title="Sales Qty (Lacs)"),
        margin=dict(l=10, r=20, t=20, b=60),
    )
    st.plotly_chart(fig_hq, use_container_width=True)

with col_div:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Division-wise Revenue Share</div>",
                unsafe_allow_html=True)
    div_data = df.groupby("Division Name", as_index=False)["Sales Amt"].sum()
    div_colors = [RED,"#cc0000","#ff4444","#990000","#ff6666",
                  "#800000","#ff8080","#660000","#ffaaaa","#4d0000"]
    fig_div = go.Figure(go.Pie(
        labels=div_data["Division Name"], values=div_data["Sales Amt"],
        hole=0.55,
        marker=dict(colors=div_colors[:len(div_data)],
                    line=dict(color="#0d0d0d", width=2)),
        textinfo="label+percent", textfont=dict(size=11, color="#eee"),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig_div.add_annotation(
        text=f"<b>{div_data.shape[0]}</b><br><span style='font-size:11px'>Divisions</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#f0f0f0", family="Nunito"),
    )
    fig_div.update_layout(
        height=340, paper_bgcolor=PAPER,
        font=dict(color=FONT, family="Nunito"),
        margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
    )
    st.plotly_chart(fig_div, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Division Revenue Trend  +  Top HQ Table
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>📋 Division Trends & Territory Rankings</span></div>",
            unsafe_allow_html=True)

col_dt, col_ht = st.columns([1.4, 1])

with col_dt:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Division Revenue Trend (Monthly)</div>",
                unsafe_allow_html=True)
    div_trend = (df.groupby(["Month_Period","Division Name"], as_index=False)["Sales Amt"].sum())
    div_trend["Label"] = div_trend["Month_Period"].apply(lambda p: pd.Period(p).strftime("%b %Y"))
    div_trend = div_trend.sort_values("Month_Period")

    fig_divtrend = go.Figure()
    div_colors_line = [RED,"#ff6b6b","#cc0000","#ff9999","#990000",
                       "#ffcccc","#800000","#ff4444","#660000","#ffaaaa"]
    for i, div in enumerate(div_trend["Division Name"].unique()):
        d = div_trend[div_trend["Division Name"] == div]
        fig_divtrend.add_trace(go.Scatter(
            x=d["Label"], y=d["Sales Amt"],
            mode="lines+markers", name=div,
            line=dict(color=div_colors_line[i % len(div_colors_line)], width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{div}</b><br>%{{x}}<br>₹%{{y:,.0f}}<extra></extra>",
        ))
    fig_divtrend.update_layout(
        height=320, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0.3)",
                    bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
        margin=dict(l=10, r=10, t=10, b=40), hovermode="x unified",
    )
    st.plotly_chart(fig_divtrend, use_container_width=True)

with col_ht:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Top Head Quarters Ranking</div>",
                unsafe_allow_html=True)
    hq_table = (
        df.groupby("Head Qtr", as_index=False)
          .agg(Revenue=("Sales Amt","sum"), Qty=("Sales Qty","sum"),
               Products=("Product Name","nunique"))
          .sort_values("Revenue", ascending=False).head(15).reset_index(drop=True)
    )
    hq_table.index   += 1
    hq_table["Revenue"] = hq_table["Revenue"].apply(fmt_inr)
    hq_table["Qty"]     = hq_table["Qty"].apply(lambda x: f"{x:,}")
    hq_table.columns    = ["Head Quarter","Revenue","Qty","SKUs"]
    st.dataframe(hq_table, use_container_width=True, height=320)


# ══════════════════════════════════════════════════════════════════════════════
# ROW 5 — Product Qty vs Revenue Scatter  +  State Qty Bar
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<div class='section-header'><span>🔬 Advanced Analysis</span></div>",
            unsafe_allow_html=True)

col_sc, col_sq = st.columns(2)

with col_sc:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Product: Revenue vs Qty (Top 30 Products)</div>",
                unsafe_allow_html=True)
    scatter_data = (df.groupby("Product Name", as_index=False)
                      .agg(Revenue=("Sales Amt","sum"), Qty=("Sales Qty","sum"))
                      .nlargest(30,"Revenue"))
    fig_sc = go.Figure(go.Scatter(
        x=scatter_data["Qty"], y=scatter_data["Revenue"],
        mode="markers+text",
        text=scatter_data["Product Name"].apply(lambda x: x[:12]+"…" if len(x)>12 else x),
        textposition="top center", textfont=dict(size=8, color="#aaa"),
        marker=dict(
            size=scatter_data["Revenue"] / scatter_data["Revenue"].max() * 30 + 8,
            color=scatter_data["Revenue"],
            colorscale=[[0,"#4a0000"],[0.5,RED],[1,"#ff6666"]],
            showscale=False,
            line=dict(color="rgba(255,255,255,0.2)", width=1),
        ),
        hovertemplate="<b>%{text}</b><br>Qty: %{x:,}<br>Revenue: ₹%{y:,.0f}<extra></extra>",
    ))
    fig_sc.update_layout(
        height=320, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=True, gridcolor=GRID, title="Sales Qty"),
        yaxis=dict(showgrid=True, gridcolor=GRID, title="Revenue (₹)"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

with col_sq:
    st.markdown("<div style='color:#aaa; font-size:0.8rem; margin-bottom:4px;'>Top 10 Head Qtrs — Sales Qty vs Revenue</div>",
                unsafe_allow_html=True)
    hq_both = (df.groupby("Head Qtr", as_index=False)
                 .agg(Revenue=("Sales Amt","sum"), Qty=("Sales Qty","sum"))
                 .nlargest(10,"Revenue").sort_values("Revenue"))

    fig_hqb = make_subplots(specs=[[{"secondary_y": True}]])
    fig_hqb.add_trace(go.Bar(
        x=hq_both["Head Qtr"], y=hq_both["Revenue"],
        name="Revenue (₹)", marker_color=RED,
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig_hqb.add_trace(go.Scatter(
        x=hq_both["Head Qtr"], y=hq_both["Qty"],
        name="Qty", mode="lines+markers",
        line=dict(color="#ff9999", width=2),
        marker=dict(size=7, color="#ff9999"),
        hovertemplate="<b>%{x}</b><br>Qty: %{y:,}<extra></extra>",
    ), secondary_y=True)
    fig_hqb.update_layout(
        height=320, paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(color=FONT, family="Nunito"),
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=GRID, title="Revenue (₹)"),
        yaxis2=dict(showgrid=False, title="Sales Qty"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0.3)"),
        margin=dict(l=10, r=10, t=10, b=60),
        barmode="group",
    )
    st.plotly_chart(fig_hqb, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# RAW DATA + CSV DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🔍 Raw Data Preview (filtered)", expanded=False):
    preview = df.drop(columns=["Month_Period","Month_Label"], errors="ignore")
    st.caption(f"Showing first 1,000 rows of **{len(preview):,}** filtered records.")
    st.dataframe(preview.head(1_000), use_container_width=True)

    # ── CSV Download button ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📥 Download Base Data")

    @st.cache_data
    def convert_to_csv(dataframe):
        return dataframe.drop(
            columns=["Month_Period","Month_Label"], errors="ignore"
        ).to_csv(index=False).encode("utf-8")

    csv_bytes = convert_to_csv(df)
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="ENTOD_Sales_Data.csv",
        mime="text/csv",
        help="Downloads the currently filtered data as a CSV file",
    )


# ── DOWNLOAD SECTION ──────────────────────────────────────────────────────────

st.markdown("---")

st.markdown("""
<div style='text-align:center;padding:15px;'>
    <h4 style='color:#f0f0f0;margin-bottom:5px;'>
        📥 Download Base Data
    </h4>
    <p style='color:#999;font-size:0.85rem;'>
        Export the currently filtered sales data in CSV format
    </p>
</div>
""", unsafe_allow_html=True)

st.info("📥 Need the source data? Click the 'Download Base CSV File' button below.")

col1, col2, col3 = st.columns([2,2,2])

with col2:
    st.download_button(
        label="⬇ Download Base CSV File",
        data=csv_bytes,
        file_name="ENTOD_Sales_Data.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='text-align:center;color:#666;font-size:12px;padding:10px;'>
        © 2026 ENTOD Pharmaceuticals | Sales Intelligence Dashboard<br>
        Data Records: {len(df):,} | Last Refresh: 10 AM & 5 PM Daily
    </div>
    """,
    unsafe_allow_html=True,
)
