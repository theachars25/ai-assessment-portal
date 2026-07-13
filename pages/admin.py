import streamlit as st
import pandas as pd
import plotly.express as px
import re
from supabase import create_client, Client

from gemini_report import generate_opportunity_report

st.set_page_config(page_title="AI Readiness Admin", page_icon="🔐", layout="wide")

# --- 1. Authentication Logic ---
def check_password():
    """Returns True if the user has entered the correct admin password."""
    def password_entered():
        if st.session_state["admin_password"] == st.secrets["admin"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["admin_password"]  # Don't keep password in state
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="admin_password")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Incorrect password 🛑")
    return False

# --- 2. Data Fetching ---
@st.cache_data(ttl=60)
def load_admin_data():
    """Fetch all assessments from Supabase."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
    
    response = supabase.table('ai_readiness_assessments').select('*').execute()
    return pd.DataFrame(response.data)

# --- 3. Text Processing for Heatmap ---
def extract_top_keywords(df, text_column, top_n=10):
    """Extracts the most common meaningful words from a text column."""
    stop_words = {"the", "and", "to", "of", "a", "in", "for", "is", "on", "that", "by", 
                  "this", "with", "i", "you", "it", "not", "or", "are", "we", "my", 
                  "tasks", "work", "time", "daily", "doing", "lot"}
    
    word_list = []
    for _, row in df.iterrows():
        dept = row['department']
        text = str(row[text_column]).lower()
        # Extract alphanumeric words > 3 characters
        words = re.findall(r'\b[a-z]{3,}\b', text)
        for w in words:
            if w not in stop_words:
                word_list.append({'department': dept, 'keyword': w})
                
    keyword_df = pd.DataFrame(word_list)
    if keyword_df.empty:
        return pd.DataFrame()
        
    # Find the overall top N keywords across all departments
    top_keywords = keyword_df['keyword'].value_counts().nlargest(top_n).index
    
    # Filter and group to get counts per department
    filtered_df = keyword_df[keyword_df['keyword'].isin(top_keywords)]
    return filtered_df.groupby(['department', 'keyword']).size().reset_index(name='count')

# --- 4. Admin UI ---
def render_admin_dashboard():
    st.title("🔐 Executive AI Readiness Dashboard")
    
    if not check_password():
        st.stop()  # Halt execution until password is correct
        
    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()

    df = load_admin_data()
    
    if df.empty:
        st.info("No data available yet.")
        st.stop()

    # Layout for Charts
    col1, col2 = st.columns(2)
    
    # --- Chart 1: AI Comfort by Department (Bar Chart) ---
    with col1:
        st.subheader("AI Comfort Across Departments")
        dept_avg = df.groupby('department', as_index=False)['ai_comfort_level'].mean()
   
        # Fixed: Mapped 'y' and labels to use 'ai_comfort_level'
        fig_bar = px.bar(
            dept_avg, 
            x='department', 
            y='ai_comfort_level', 
            color='department',
            labels={'department': 'Department', 'ai_comfort_level': 'Avg Comfort Level (1-5)'},
            text_auto='.1f'
        )
        fig_bar.update_yaxes(range=[0, 5])
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Chart 2: Time Sink Heatmap ---
    with col2:
        st.subheader("Time Sink Heatmap")
        st.caption("Most frequent bottleneck keywords by department.")
        
        # Fixed: Updated column target from 'time_consuming_tasks' to 'time_sinks'
        heatmap_data = extract_top_keywords(df, 'time_sinks', top_n=12)
        
        if not heatmap_data.empty:
            fig_heat = px.density_heatmap(
                heatmap_data, 
                x="keyword", 
                y="department", 
                z="count",
                color_continuous_scale="Reds",
                labels={'keyword': 'Reported Task/Keyword', 'department': 'Department', 'count': 'Frequency'}
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.write("Not enough qualitative data to generate heatmap.")

    st.markdown("---")
    st.subheader("🧠 AI Strategy Consultant")
    st.write("Generate a custom AI readiness report based on the qualitative feedback from your team.")
    
    # Extract and format the qualitative data
    if not df.empty:
        company_name = df['company_name'].iloc[0] 
        
        # Combine the time_sinks into a single text block, labeled by department
        feedback_texts = []
        for _, row in df.iterrows():
            dept = row['department']
            # Fixed: Updated from 'time_consuming_tasks' to 'time_sinks'
            task = row['time_sinks']
            if pd.notna(task) and str(task).strip():
                feedback_texts.append(f"- [{dept}]: {task}")
        
        aggregated_feedback = "\n".join(feedback_texts)
        
        # 1. Generate Report Button
        if st.button("Generate Executive Report", type="primary"):
            if len(feedback_texts) < 2:
                st.warning("Not enough qualitative feedback to generate a meaningful report yet.")
            else:
                with st.spinner("Analyzing cross-departmental bottlenecks with Gemini..."):
                    try:
                        api_key = st.secrets["gemini"]["api_key"]
                        report_md = generate_opportunity_report(
                            company_name, 
                            aggregated_feedback, 
                            api_key
                        )
                        # Save to session state so it survives app reruns (like clicking download)
                        st.session_state['generated_report'] = report_md
                    except Exception as e:
                        st.error(f"Failed to generate report: {e}")

        # 2. Display and Download Report
        if 'generated_report' in st.session_state:
            st.success("Report generated successfully!")
            
            with st.expander("Preview Report", expanded=True):
                st.markdown(st.session_state['generated_report'])
                
            st.download_button(
                label="📥 Download Report (.md)",
                data=st.session_state['generated_report'],
                file_name=f"{company_name.replace(' ', '_')}_AI_Opportunity_Analysis.md",
                mime="text/markdown"
            )

render_admin_dashboard()