import streamlit as st
from supabase import create_client, Client
import uuid

# ==========================================
# 1. Configuration & Database Initialization
# ==========================================
st.set_page_config(page_title="AI Readiness Assessment", page_icon="🚀", layout="centered")

@st.cache_resource
def init_connection() -> Client:
    """Initialize the Supabase client using Streamlit secrets."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# 2. Session State Management
# ==========================================
# Initialize session state variables if they don't exist
if 'step' not in st.session_state:
    st.session_state.step = 1

# Comprehensive form fields tracking the 11 questions
form_fields = [
    'company_name',          # Q1 (Context)
    'department',            # Q1
    'job_title',             # Q2
    'ai_comfort_level',      # Q3
    'time_sinks',            # Q4
    'weekly_time_percentage',# Q5
    'high_value_shift',      # Q6
    'usage_frequency',       # Q7
    'current_ai_tools',      # Q8
    'shadow_ai_exposure',    # Q9
    'adoption_barriers',     # Q10
    'training_desires'       # Q11
]

for field in form_fields:
    if field not in st.session_state:
        # Default structures based on response types (lists for multiselects/checkboxes)
        if field in ['current_ai_tools', 'adoption_barriers']:
            st.session_state[field] = []
        elif field == 'ai_comfort_level':
            st.session_state[field] = 3
        else:
            st.session_state[field] = ""

# Navigation functions
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# ==========================================
# 3. Wizard UI Components
# ==========================================
st.title("Corporate AI Readiness Assessment")
st.progress(st.session_state.step / 4, text=f"Step {st.session_state.step} of 4")

# --- MODULE 1: Profile & Demographics ---
if st.session_state.step == 1:
    st.subheader("📋 Module 1: Profile & Baseline")
    
    st.session_state.company_name = st.text_input(
        "Company Name", 
        value=st.session_state.company_name,
        placeholder="Enter your organization's name"
    )
    
    # Pre-aligned with corporate pillars (like FSD Africa)
    departments = ["Research", "Programmes", "Investment", "Communications", "Leadership", "Operations", "Support", "Other"]
    dept_index = departments.index(st.session_state.department) if st.session_state.department in departments else 0
    st.session_state.department = st.selectbox(
        "1. What is your department or functional area?", 
        options=departments,
        index=dept_index
    )
    
    st.session_state.job_title = st.text_input(
        "2. What is your specific job title/role?", 
        value=st.session_state.job_title,
        placeholder="e.g., Investment Analyst, Operations Manager"
    )
    
    st.session_state.ai_comfort_level = st.slider(
        "3. How would you rate your current comfort level with using Generative AI tools?",
        min_value=1, 
        max_value=5, 
        value=st.session_state.ai_comfort_level,
        step=1,
        help="1 = Never used them | 3 = Occasional use for basic tasks | 5 = Power user (daily workflow integration)"
    )

    # Validation: Profile basics are mandatory
    if st.button("Next ➡️"):
        if not st.session_state.company_name.strip() or not st.session_state.job_title.strip():
            st.error("Please fill in your Company Name and Job Title to continue.")
        else:
            next_step()
            st.rerun()

# --- MODULE 2: Friction & Time Audit ---
elif st.session_state.step == 2:
    st.subheader("⏳ Module 2: Time Sink & Friction Audit")
    
    st.session_state.time_sinks = st.text_area(
        "4. What are the top 2 most repetitive, tedious, or time-consuming tasks you handle in an average work week?",
        value=st.session_state.time_sinks,
        placeholder="e.g., Summarizing 50-page investment reports, drafting weekly newsletter copy, manual data entry from PDFs into Excel...",
        height=100
    )
    
    time_percentages = ["0-10%", "11-25%", "26-50%", "51%+"]
    tp_index = time_percentages.index(st.session_state.weekly_time_percentage) if st.session_state.weekly_time_percentage in time_percentages else 0
    st.session_state.weekly_time_percentage = st.selectbox(
        "5. Roughly what percentage of your total weekly working hours is spent on these repetitive tasks?",
        options=time_percentages,
        index=tp_index
    )
    
    st.session_state.high_value_shift = st.text_area(
        "6. If an AI tool handled those specific tasks flawlessly, what high-value work would you focus on instead?",
        value=st.session_state.high_value_shift,
        placeholder="e.g., Deeper strategic research, more face-to-face client relationship management...",
        height=100
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back", on_click=prev_step)
    with col2:
        if st.button("Next ➡️"):
            if not st.session_state.time_sinks.strip() or not st.session_state.high_value_shift.strip():
                st.error("Please provide brief answers to help map out your workflows.")
            else:
                next_step()
                st.rerun()

# --- MODULE 3: Shadow AI & Behavior ---
elif st.session_state.step == 3:
    st.subheader("🛡️ Module 3: Tool Behavior & Shadow AI Risk")
    
    frequencies = ["Yes, daily", "Yes, a few times a week", "Rarely", "Never"]
    freq_index = frequencies.index(st.session_state.usage_frequency) if st.session_state.usage_frequency in frequencies else 0
    st.session_state.usage_frequency = st.selectbox(
        "7. Do you currently use AI tools (approved or unapproved) to help you do your job?",
        options=frequencies,
        index=freq_index
    )
    
    common_tools = ["Company-provided / Enterprise tools", "Public/Free ChatGPT", "Claude", "Midjourney", "Grammarly", "None / Other"]
    st.session_state.current_ai_tools = st.multiselect(
        "8. Which AI tools do you use most often? (Select all that apply)",
        options=common_tools,
        default=st.session_state.current_ai_tools
    )
    
    shadow_options = ["", "Yes", "No", "Unsure if the data counts as sensitive"]
    shadow_index = shadow_options.index(st.session_state.shadow_ai_exposure) if st.session_state.shadow_ai_exposure in shadow_options else 0
    st.session_state.shadow_ai_exposure = st.selectbox(
        "9. Have you ever pasted internal documents, data, or client info into a public/free AI tool to get a faster result?",
        options=shadow_options,
        index=shadow_index,
        help="This response is confidential and anonymized to calculate institutional data security exposure."
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back", on_click=prev_step)
    with col2:
        if st.button("Next ➡️"):
            if not st.session_state.shadow_ai_exposure:
                st.error("Please select an answer for Question 9 to assess corporate guardrail exposure.")
            else:
                next_step()
                st.rerun()

# --- MODULE 4: Barriers & Training Desires ---
elif st.session_state.step == 4:
    st.subheader("🚀 Module 4: Adoption Barriers & Training Blueprint")
    
    barrier_options = [
        "I don't know what tools are allowed or safe to use.",
        "I don't know how to write good prompts to get accurate results.",
        "I tried it, but the output felt generic or inaccurate.",
        "I don't think AI applies to the type of complex work I do."
    ]
    st.session_state.adoption_barriers = st.multiselect(
        "10. What is holding you back from using AI more effectively right now? (Select all that apply)",
        options=barrier_options,
        default=st.session_state.adoption_barriers
    )
    
    training_options = [
        "Foundations (How it works, basic prompting)",
        "Advanced Prompting (Getting precise, domain-specific outputs)",
        "Agentic AI (Building multi-step workflows or custom assistants)"
    ]
    t_index = training_options.index(st.session_state.training_desires) if st.session_state.training_desires in training_options else 0
    st.session_state.training_desires = st.selectbox(
        "11. Which AI concept are you most interested in learning to apply directly to your role?",
        options=training_options,
        index=t_index
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back", on_click=prev_step)
    with col2:
        if st.button("Submit Assessment 🚀", type="primary"):
            
            # Form Data Payload Mapping
            payload = {
                "user_id": str(uuid.uuid4()), 
                "company_name": st.session_state.company_name,
                "department": st.session_state.department,
                "job_title": st.session_state.job_title,
                "ai_comfort_level": st.session_state.ai_comfort_level,
                "time_sinks": st.session_state.time_sinks,
                "weekly_time_percentage": st.session_state.weekly_time_percentage,
                "high_value_shift": st.session_state.high_value_shift,
                "usage_frequency": st.session_state.usage_frequency,
                "current_ai_tools": st.session_state.current_ai_tools,
                "shadow_ai_exposure": st.session_state.shadow_ai_exposure,
                "adoption_barriers": st.session_state.adoption_barriers,
                "training_desires": st.session_state.training_desires
            }
            
            # Database Submission
            try:
                with st.spinner("Submitting your assessment..."):
                    supabase.table('ai_readiness_assessments').insert(payload).execute()
                    
                st.success("Assessment submitted successfully! Thank you.")
                st.balloons()
                
                # Reset wizard state completely
                st.session_state.step = 1
                for field in form_fields:
                    del st.session_state[field]
                st.rerun()
                    
            except Exception as e:
                st.error(f"An error occurred while submitting: {str(e)}")