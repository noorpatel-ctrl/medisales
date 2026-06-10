import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration & Theme Initialization
st.set_page_config(
    page_title="ENTOD Executive Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI/UX & Card Alignment
st.markdown("""
    <style>
        /* Main App Background & Font tweaks */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Custom KPI Card Styling */
        .kpi-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid #eef2f6;
            text-align: center;
            margin-bottom: 10px;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 1.6rem;
            color: #0f172a;
            font-weight: 700;
        }
        /* Style Section Headers */
        .section-header {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1e293b;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f1f5f9;
        }
    </style>
""", unsafe_allow_html=True)


# 2. Cached Data Loading
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Data.xlsb", engine="pyxlsb")
        if pd.api.types.is_numeric_dtype(df["Month"]):
            df["Month"] = pd.to_datetime(df["Month"].astype(int), unit="D", origin="1899-12-30")
        df["Month"] = pd.to_datetime(df["Month"])
        df["Month_Period"] = df["Month"].dt.to_period("M")
        return df
    except Exception as e:
        st.error(f"Error loading Data.xlsb: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.warning("No data found or Data.xlsb failed to load. Please verify the source file.")
    st.stop()


# 3. Sidebar Filter Panel
with st.sidebar:
    st.title("🎛️ Control Panel")
    st.markdown("Use filters below to isolate specific markets or product groups.")
    st.write("---")
    
    state = st.multiselect("Select State Name", sorted(df_raw["State Name"].dropna().unique()))
    division = st.multiselect("Select Division Name", sorted(df_raw["Division Name"].dropna().unique()))


# 4. Filter Application
df = df_raw.copy()
if state:
    df = df[df["State Name"].isin(state)]
if division:
    df = df[df["Division Name"].isin(division)]


# 5. Header Section
st.markdown("<h1 style='margin-bottom: 0;'>ENTOD Commercial Performance Dashboard</h1>", unsafe_allow_html=True)
st.caption("📈 Real-time Executive Sales Intelligence Platform")
st.write("")


# 6. KPI Metrics Generation
if not df.empty:
    total_rev = df["Sales Amt"].sum()
    total_qty = df["Sales Qty"].sum()
    
    # Defensive checks if grouping returns empty series
    prod_grouped = df.groupby("Product Name")["Sales Amt"].sum()
    top_product = prod_grouped.idxmax() if not prod_grouped.empty else "N/A"
    
    state_grouped = df.groupby("State Name")["Sales Amt"].sum()
    top_state = state_grouped.idxmax() if not state_grouped.empty else "N/A"
else:
    total_rev, total_qty, top_product, top_state = 0, 0, "N/A", "N/A"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">₹{total_rev:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Volume Sold</div>
            <div class="kpi-value">{total_qty:,.0f} <span style="font-size:1rem; font-weight:normal; color:#94a3b8;">units</span></div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Top Performer Product</div>
            <div class="kpi-value" style="font-size: 1.25rem; padding-top: 4px;">{top_product}</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Top Performer State</div>
            <div class="kpi-value" style="font-size: 1.25rem; padding-top: 4px;">{top_state}</div>
        </div>
    """, unsafe_allow_html=True)


# 7. Chart Visualizations Section
if df.empty:
    st.info("The current filter selections yield no data. Please adjust your criteria.")
else:
    # --- Trend Chart ---
    st.markdown("<div class='section-header'>Revenue Trajectory Over Time</div>", unsafe_allow_html=True)
    trend = df.groupby("Month_Period")["Sales Amt"].sum().reset_index()
    trend["Month_Period"] = trend["Month_Period"].astype(str)
    
    fig_trend = px.line(
        trend, 
        x="Month_Period", 
        y="Sales Amt",
        labels={"Month_Period": "Timeline (Months)", "Sales Amt": "Revenue (₹)"},
        markers=True,
        color_discrete_sequence=["#0284c7"]
    )
    fig_trend.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=10, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='#f1f5f9')
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Side-by-Side Breakdown Charts ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='section-header'>Top 10 High-Contribution Products</div>", unsafe_allow_html=True)
        prod = df.groupby("Product Name")["Sales Amt"].sum().nlargest(10).reset_index()
        
        fig_prod = px.bar(
            prod, 
            x="Sales Amt", 
            y="Product Name", 
            orientation="h",
            labels={"Sales Amt": "Revenue (₹)", "Product Name": ""},
            color="Sales Amt",
            color_continuous_scale="Blues"
        )
        fig_prod.update_layout(
            yaxis={'categoryorder':'total ascending'},
            margin=dict(l=20, r=20, t=10, b=20),
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_prod, use_container_width=True)
        
    with col2:
        st.markdown("<div class='section-header'>Top 10 Target Territory Markets</div>", unsafe_allow_html=True)
        states = df.groupby("State Name")["Sales Amt"].sum().nlargest(10).reset_index()
        
        fig_state = px.bar(
            states, 
            x="Sales Amt", 
            y="State Name", 
            orientation="h",
            labels={"Sales Amt": "Revenue (₹)", "State Name": ""},
            color="Sales Amt",
            color_continuous_scale="Purples"
        )
        fig_state.update_layout(
            yaxis={'categoryorder':'total ascending'},
            margin=dict(l=20, r=20, t=10, b=20),
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_state, use_container_width=True)


# 8. Actionable Footer / Export Utility
st.write("---")
col_footer, col_btn = st.columns([4, 1])
with col_footer:
    st.caption("Data source extraction optimized for pyxlsb compression formats.")
with col_btn:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Filtered Dataset", 
        data=csv, 
        file_name="ENTOD_Filtered_Sales_Data.csv", 
        mime="text/csv",
        use_container_width=True
    )