import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# ==========================================
# 1. Configuration & Database Connection
# ==========================================
st.set_page_config(page_title="AI Assessment Dashboard", page_icon="📊", layout="wide")

@st.cache_resource
def init_connection() -> Client:
    """Initialize the Supabase client using Streamlit secrets."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# 2. Fetch Data from Supabase
# ==========================================
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def load_data():
    try:
        # Fetch all rows from the new table structure
        response = supabase.table('ai_readiness_assessments').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 3. Render Dashboard UI
# ==========================================
st.title("🛡️ AI Opportunity & Readiness Analytics")
st.markdown("Executive insights mapped out from organizational assessments.")

if df.empty:
    st.info("Waiting for assessments to be submitted... Go complete a form first!")
else:
    # --- Top-Level Executive Metrics KPI Blocks ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Responses Evaluated", value=len(df))
    
    with col2:
        # Fixed column name mismatch here (changed from ai_familiarity to ai_comfort_level)
        avg_comfort = df['ai_comfort_level'].mean()
        st.metric(label="Org-Wide AI Comfort Level (Out of 5)", value=f"{avg_comfort:.2f}")
        
    with col3:
        # Calculate exposure metric based on "Yes" or "Unsure" responses to Question 9
        shadow_ai_count = df[df['shadow_ai_exposure'].isin(['Yes', 'Unsure if the data counts as sensitive'])].shape[0]
        exposure_pct = (shadow_ai_count / len(df)) * 100
        st.metric(label="Data Vulnerability / Shadow AI Risk", value=f"{exposure_pct:.1f}%")

    st.markdown("---")

    # --- Charts & Insights Layout ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Department AI Comfort Benchmark")
        # Aggregates average comfort scores by department
        dept_comfort = df.groupby('department')['ai_comfort_level'].mean().reset_index()
        fig_comfort = px.bar(
            dept_comfort, 
            x='department', 
            y='ai_comfort_level',
            labels={'department': 'Department', 'ai_comfort_level': 'Avg Comfort (1-5)'},
            color='ai_comfort_level',
            color_continuous_scale=px.colors.sequential.Bluyl
        )
        st.plotly_chart(fig_comfort, use_container_width=True)

    with chart_col2:
        st.subheader("Operational Friction Metrics")
        # Visualizes the time spent on repetitive tasks
        time_sink_dist = df['weekly_time_percentage'].value_counts().reset_index()
        time_sink_dist.columns = ['Weekly Time Lost', 'Employee Count']
        fig_time = px.pie(
            time_sink_dist, 
            names='Weekly Time Lost', 
            values='Employee Count',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # --- The Qualitative Data View (Use Case Goldmine) ---
    st.markdown("---")
    st.subheader("💡 Process Automation Bottlenecks & Raw Feedback")
    
    # Simple search filter by department
    selected_dept = st.selectbox("Filter bottlenecks by department:", ["All"] + list(df['department'].unique()))
    
    filtered_df = df if selected_dept == "All" else df[df['department'] == selected_dept]
    
    st.dataframe(
        filtered_df[['job_title', 'department', 'time_sinks', 'high_value_shift']],
        column_config={
            "job_title": "Role",
            "department": "Department",
            "time_sinks": "Reported Core Bottlenecks & Time Sinks",
            "high_value_shift": "Pivot Priority (If Automated)"
        },
        use_container_width=True,
        hide_index=True
    )