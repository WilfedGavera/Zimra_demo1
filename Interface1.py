import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="ZIMRA Audit Command Center", layout="wide")

# Custom CSS for ZIMRA Branding
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #004d00; color: white; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("zimra_data.csv")
    
    # CALCULATE RISK QUADRANT (New Choice)
    # High Impact = Top 25% of Revenue
    rev_threshold = df['annual_revenue_usd'].quantile(0.75)
    
    def define_quadrant(row):
        is_high_risk = row['prediction_score'] >= 70
        is_high_impact = row['annual_revenue_usd'] >= rev_threshold
        
        if is_high_risk and is_high_impact: return "🔥 High Risk / High Impact"
        elif is_high_risk: return "⚠️ High Risk / Low Impact"
        elif is_high_impact: return "💰 Low Risk / High Impact"
        return "✅ Low Risk / Low Impact"
        
    df['risk_quadrant'] = df.apply(define_quadrant, axis=1)
    return df

df = load_data()

# --- SIDEBAR: USER CHOICES ---
st.sidebar.title("🇿🇼 Audit Selection")
st.sidebar.info("Configure your audit criteria below.")

# 1. Choose the Feature to Display
available_columns = [
    'sector', 'region', 'annual_revenue_usd', 'late_filings_last_12m', 
    'fiscal_device_uptime_pct', 'vat_to_sales_ratio', 'outstanding_debt_zig', 
    'previous_audit_violations', 'risk_quadrant'
]
feature_choice = st.sidebar.selectbox("Inspect BISEP Feature:", available_columns)

# 2. Filter Category
filter_mode = st.sidebar.radio(
    "Selection Mode:",
    ["All Records", "Likely to Default (Score > 50%)", "By Risk Quadrant"]
)

# --- LOGIC ---
filtered_df = df.copy()

if filter_mode == "Likely to Default (Score > 50%)":
    filtered_df = filtered_df[filtered_df['prediction_score'] > 50]

elif filter_mode == "By Risk Quadrant":
    q_choice = st.sidebar.selectbox("Choose Quadrant:", df['risk_quadrant'].unique())
    filtered_df = filtered_df[filtered_df['risk_quadrant'] == q_choice]

# --- MAIN DASHBOARD ---
st.title("🛡️ ZIMRA Risk Intelligence Portal")

# KPI Summary Row
m1, m2, m3 = st.columns(3)
m1.metric("Selected Cases", len(filtered_df))
m2.metric("Avg. Risk Score", f"{filtered_df['prediction_score'].mean():.1f}%")
m3.metric("Revenue at Stake", f"${filtered_df['annual_revenue_usd'].sum():,.0f}")

st.divider()

# Results Section
st.subheader(f"Results: {filter_mode}")

# Display columns requested: Name + ID + Feature Chosen + Prediction Score
display_cols = ['taxpayer_name', 'taxpayer_id', feature_choice, 'prediction_score']

# Using progress bars for the prediction score to make it "Pro"
st.dataframe(
    filtered_df[display_cols].sort_values("prediction_score", ascending=False),
    column_config={
        "prediction_score": st.column_config.ProgressColumn(
            "Prediction Score", format="%d%%", min_value=0, max_value=100
        ),
        "annual_revenue_usd": st.column_config.NumberColumn("Revenue (USD)", format="$%d"),
    },
    use_container_width=True
)

# Visualizing the Quadrants
st.divider()
st.subheader("Regional Risk Breakdown")
fig = px.bar(filtered_df, x='region', y='prediction_score', color='sector', barmode='group')
st.plotly_chart(fig, use_container_width=True)