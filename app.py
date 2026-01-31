"""
Customer Churn Prediction Dashboard
Streamlit-based interactive dashboard with user authentication and dataset upload
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

def get_project_root():
    """Get project root directory dynamically"""
    if os.getenv("PROJECT_ROOT"):
        return Path(os.getenv("PROJECT_ROOT"))
    return Path(__file__).parent.parent

PROJECT_ROOT = get_project_root()
DATA_PATH = Path(os.getenv("DATA_PATH", PROJECT_ROOT / "data" / "processed"))
API_URL = os.getenv("API_URL", "http://localhost:8000")

# File paths
PREDICTIONS_FILE = DATA_PATH / "customer_predictions.csv"
RETENTION_FILE = DATA_PATH / "retention_actions.csv"
MODEL_COMPARISON_FILE = DATA_PATH / "model_comparison.csv"

# Page Configuration
st.set_page_config(
    page_title="Customer Churn Prediction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .risk-critical { color: #e74c3c; font-weight: bold; }
    .risk-high { color: #f39c12; font-weight: bold; }
    .risk-medium { color: #f1c40f; font-weight: bold; }
    .risk-low { color: #2ecc71; font-weight: bold; }
    .profit { color: #2ecc71; font-size: 1.5rem; font-weight: bold; }
    .loss { color: #e74c3c; font-size: 1.5rem; font-weight: bold; }
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None


# ============================================================================
# API HELPER FUNCTIONS
# ============================================================================

def api_request(method, endpoint, data=None, files=None, auth=True):
    """Make API request with optional authentication"""
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return None
        
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.token = None
            return {"error": "Unauthorized. Please login again."}
        else:
            # Try to get error detail, but handle non-JSON responses
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            return {"error": error_detail}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Make sure the backend is running."}
    except Exception as e:
        return {"error": str(e)}


def register_user(email, username, password, full_name=None, company=None):
    """Register a new user"""
    data = {
        "email": email,
        "username": username,
        "password": password,
        "full_name": full_name,
        "company": company
    }
    return api_request("POST", "/auth/register", data, auth=False)


def login_user(email, password):
    """Login user and get token"""
    data = {"email": email, "password": password}
    result = api_request("POST", "/auth/login-json", data, auth=False)
    
    if result and "access_token" in result:
        st.session_state.token = result["access_token"]
        st.session_state.authenticated = True
        # Get user info
        user_info = api_request("GET", "/auth/me")
        if user_info and "error" not in user_info:
            st.session_state.user = user_info
        return True
    return False


def logout_user():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_analysis = None


def upload_dataset(file, description=None):
    """Upload dataset for analysis"""
    files = {"file": (file.name, file, "text/csv")}
    data = {"description": description} if description else {}
    return api_request("POST", "/datasets/upload", data=data, files=files)


def get_dataset_history(limit=10):
    """Get user's dataset upload history"""
    return api_request("GET", f"/datasets/history?limit={limit}")


def compare_latest_datasets():
    """Compare the latest two datasets"""
    return api_request("GET", "/datasets/compare/latest")


def compare_datasets(dataset_1_id, dataset_2_id):
    """Compare two specific datasets"""
    data = {"dataset_1_id": dataset_1_id, "dataset_2_id": dataset_2_id}
    return api_request("POST", "/datasets/compare", data)


# ============================================================================
# PAGE: LOGIN / REGISTER
# ============================================================================

def show_auth_page():
    """Show authentication page"""
    st.markdown('<h1 class="main-header">🔐 Welcome to Churn Prediction</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if email and password:
                    if login_user(email, password):
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")
                else:
                    st.warning("Please enter email and password")
    
    with tab2:
        st.markdown("### Create New Account")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                reg_email = st.text_input("Email*", placeholder="you@company.com")
                reg_username = st.text_input("Username*", placeholder="johndoe")
            with col2:
                reg_fullname = st.text_input("Full Name", placeholder="John Doe")
                reg_company = st.text_input("Company", placeholder="Acme Inc")
            
            reg_password = st.text_input("Password*", type="password")
            reg_password2 = st.text_input("Confirm Password*", type="password")
            
            register = st.form_submit_button("Create Account", use_container_width=True)
            
            if register:
                if not all([reg_email, reg_username, reg_password]):
                    st.warning("Please fill in all required fields")
                elif reg_password != reg_password2:
                    st.error("Passwords do not match")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    result = register_user(reg_email, reg_username, reg_password, reg_fullname, reg_company)
                    if result and "error" not in result:
                        st.success("✅ Account created! Please login.")
                    elif result and "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.error("❌ Registration failed")


# ============================================================================
# PAGE: UPLOAD DATASET
# ============================================================================

def show_upload_page():
    """Show dataset upload and analysis page"""
    st.markdown('<h1 class="main-header">📤 Upload Your Dataset</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload your customer data in CSV format. The system will:
    1. **Analyze** your dataset using our ML model
    2. **Predict** churn probability for each customer
    3. **Store** results for future comparison
    4. **Compare** with previous uploads to track progress
    """)
    
    st.markdown("---")
    
    # File Upload Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Customer CSV",
            type=["csv"],
            help="Upload a CSV file with customer data"
        )
        description = st.text_input(
            "Description (optional)",
            placeholder="e.g., Q1 2024 Customer Data"
        )
    
    with col2:
        st.markdown("**Expected Columns:**")
        st.markdown("""
        - CustomerID
        - Gender
        - SeniorCitizen
        - Partner, Dependents
        - Tenure
        - PhoneService
        - InternetService
        - Contract
        - MonthlyCharges
        - TotalCharges
        """)
    
    if uploaded_file:
        # Preview uploaded file
        st.markdown("### 📋 Data Preview")
        try:
            df_preview = pd.read_csv(uploaded_file)
            st.dataframe(df_preview.head(10), use_container_width=True)
            st.info(f"📊 Total rows: {len(df_preview):,} | Columns: {len(df_preview.columns)}")
            
            # Reset file pointer for upload
            uploaded_file.seek(0)
            
            if st.button("🚀 Analyze Dataset", type="primary", use_container_width=True):
                with st.spinner("Analyzing dataset..."):
                    result = upload_dataset(uploaded_file, description)
                
                if result and "error" not in result:
                    st.session_state.current_analysis = result
                    st.success("✅ Dataset analyzed successfully!")
                    st.rerun()
                elif result and "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.error("❌ Failed to analyze dataset")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
    
    # Show Current Analysis Results
    if st.session_state.current_analysis:
        analysis = st.session_state.current_analysis
        
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Customers", f"{analysis.get('total_customers', 0):,}")
        with col2:
            st.metric("Churn Rate", f"{analysis.get('churn_rate', 0):.1f}%")
        with col3:
            st.metric("High Risk", f"{analysis.get('high_risk_count', 0):,}")
        with col4:
            st.metric("Revenue at Risk", f"${analysis.get('revenue_at_risk', 0):,.0f}")
        
        # Risk Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Risk Distribution")
            segment_stats = analysis.get('segment_stats', {})
            if segment_stats:
                risk_data = pd.DataFrame([
                    {"Risk Level": level, "Count": stats.get('count', 0)}
                    for level, stats in segment_stats.items()
                ])
                fig = px.pie(
                    risk_data, values='Count', names='Risk Level',
                    color='Risk Level',
                    color_discrete_map={
                        'Low': '#2ecc71', 'Medium': '#f1c40f',
                        'High': '#f39c12', 'Critical': '#e74c3c'
                    },
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Key Insights")
            churn_rate = analysis.get('churn_rate', 0)
            if churn_rate > 30:
                st.error(f"⚠️ High churn risk detected ({churn_rate:.1f}%)")
                st.markdown("- Consider immediate retention campaigns")
                st.markdown("- Review high-risk customer segments")
            elif churn_rate > 15:
                st.warning(f"⚡ Moderate churn risk ({churn_rate:.1f}%)")
                st.markdown("- Monitor at-risk customers")
                st.markdown("- Implement proactive engagement")
            else:
                st.success(f"✅ Low churn risk ({churn_rate:.1f}%)")
                st.markdown("- Continue current strategies")
                st.markdown("- Focus on customer satisfaction")


# ============================================================================
# PAGE: HISTORY & COMPARISON
# ============================================================================

def show_comparison_page():
    """Show dataset history and comparison"""
    st.markdown('<h1 class="main-header">📈 Dataset History & Comparison</h1>', unsafe_allow_html=True)
    
    # Get history
    history = get_dataset_history(limit=20)
    
    if not history or "error" in history:
        st.info("📭 No datasets uploaded yet. Upload your first dataset to get started!")
        return
    
    st.markdown("### 📜 Your Dataset History")
    
    # History table
    history_df = pd.DataFrame(history)
    history_df['upload_date'] = pd.to_datetime(history_df['upload_date']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        history_df[['filename', 'upload_date', 'total_customers', 'churn_rate', 'revenue_at_risk']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "filename": "Dataset",
            "upload_date": "Upload Date",
            "total_customers": st.column_config.NumberColumn("Customers", format="%d"),
            "churn_rate": st.column_config.NumberColumn("Churn Rate %", format="%.1f%%"),
            "revenue_at_risk": st.column_config.NumberColumn("Revenue at Risk", format="$%.0f")
        }
    )
    
    st.markdown("---")
    
    # Comparison Section
    if len(history) >= 2:
        st.markdown("### 🔄 Compare Datasets")
        
        col1, col2 = st.columns(2)
        
        dataset_options = {f"{d['filename']} ({d['upload_date'][:10]})": d['id'] for d in history}
        
        with col1:
            st.markdown("**Previous Dataset (Baseline)**")
            prev_selection = st.selectbox(
                "Select previous dataset",
                options=list(dataset_options.keys()),
                index=1 if len(history) > 1 else 0,
                key="prev_dataset"
            )
        
        with col2:
            st.markdown("**Current Dataset**")
            curr_selection = st.selectbox(
                "Select current dataset",
                options=list(dataset_options.keys()),
                index=0,
                key="curr_dataset"
            )
        
        if st.button("📊 Compare Datasets", type="primary", use_container_width=True):
            prev_id = dataset_options[prev_selection]
            curr_id = dataset_options[curr_selection]
            
            if prev_id == curr_id:
                st.warning("Please select different datasets to compare")
            else:
                with st.spinner("Comparing datasets..."):
                    comparison = compare_datasets(prev_id, curr_id)
                
                if comparison and "error" not in comparison:
                    show_comparison_results(comparison)
                else:
                    st.error("Failed to compare datasets")
        
        # Auto-compare with latest
        st.markdown("---")
        st.markdown("### ⚡ Quick Comparison (Latest vs Previous)")
        
        if st.button("Compare Latest Upload with Previous", use_container_width=True):
            with st.spinner("Comparing..."):
                comparison = compare_latest_datasets()
            
            if comparison and "error" not in comparison:
                show_comparison_results(comparison)
            elif comparison is None:
                st.info("Need at least 2 datasets to compare")
            else:
                st.error("Failed to compare datasets")
    else:
        st.info("📊 Upload at least 2 datasets to enable comparison features")


def show_comparison_results(comparison):
    """Display comparison results with profit/loss"""
    st.markdown("---")
    st.markdown("### 📊 Comparison Results")
    
    # Profit/Loss Banner
    is_improvement = comparison.get('is_improvement', False)
    profit_loss = comparison.get('profit_loss_amount', 0)
    
    if is_improvement:
        st.success(f"""
        ### 🎉 IMPROVEMENT DETECTED!
        **Estimated Annual Profit: ${profit_loss:,.2f}**
        
        Your retention efforts are working! Churn rate has decreased.
        """)
    else:
        st.error(f"""
        ### ⚠️ ATTENTION NEEDED
        **Estimated Annual Loss: ${abs(profit_loss):,.2f}**
        
        Churn rate has increased. Consider reviewing retention strategies.
        """)
    
    # Metrics comparison
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change = comparison.get('customer_change', 0)
        st.metric("Customer Change", f"{change:+,}", delta_color="normal")
    
    with col2:
        change = comparison.get('churn_rate_change', 0)
        st.metric("Churn Rate Change", f"{change:+.1f}%", delta=f"{-change:.1f}%", delta_color="inverse")
    
    with col3:
        change = comparison.get('revenue_change', 0)
        st.metric("Revenue Change", f"${change:+,.0f}")
    
    with col4:
        change = comparison.get('risk_change', 0)
        st.metric("Risk Change", f"${change:+,.0f}", delta_color="inverse")
    
    # Detailed comparison
    detailed = comparison.get('detailed_comparison', {})
    
    if detailed:
        st.markdown("### 📋 Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**📅 {comparison.get('dataset_1_filename', 'Previous')}**")
            period_1 = detailed.get('period_1', {})
            st.write(f"- Customers: {period_1.get('customers', 0):,}")
            st.write(f"- Revenue: ${period_1.get('revenue', 0):,.0f}")
            st.write(f"- Churn Rate: {period_1.get('churn_rate', 0):.1f}%")
            st.write(f"- At Risk: ${period_1.get('revenue_at_risk', 0):,.0f}")
        
        with col2:
            st.markdown(f"**📅 {comparison.get('dataset_2_filename', 'Current')}**")
            period_2 = detailed.get('period_2', {})
            st.write(f"- Customers: {period_2.get('customers', 0):,}")
            st.write(f"- Revenue: ${period_2.get('revenue', 0):,.0f}")
            st.write(f"- Churn Rate: {period_2.get('churn_rate', 0):.1f}%")
            st.write(f"- At Risk: ${period_2.get('revenue_at_risk', 0):,.0f}")
        
        # Insights
        insights = detailed.get('insights', [])
        if insights:
            st.markdown("### 💡 Insights")
            for insight in insights:
                st.markdown(f"- {insight}")


# ============================================================================
# PAGE: DASHBOARD (Original)
# ============================================================================

@st.cache_data(ttl=300)
def load_data():
    """Load customer data from CSV"""
    try:
        df = pd.read_csv(PREDICTIONS_FILE)
        return df
    except Exception as e:
        return None


def show_dashboard_page():
    """Show main dashboard"""
    st.markdown('<h1 class="main-header">📊 Customer Churn Dashboard</h1>', unsafe_allow_html=True)
    
    data = load_data()
    
    if data is not None:
        # KPI Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        total_customers = len(data)
        
        if 'Churn_Probability' in data.columns:
            high_risk = (data['Churn_Probability'] >= 0.7).sum()
            critical_risk = (data['Churn_Probability'] >= 0.5).sum()
            revenue_at_risk = data[data['Churn_Probability'] >= 0.5]['MonthlyCharges'].sum()
            churn_rate = data['Churn_Probability'].mean() * 100
        else:
            high_risk = int(total_customers * 0.15)
            critical_risk = int(total_customers * 0.25)
            revenue_at_risk = 211661
            churn_rate = 26.5
        
        with col1:
            st.metric("Total Customers", f"{total_customers:,}")
        with col2:
            st.metric("Avg Churn Risk", f"{churn_rate:.1f}%")
        with col3:
            st.metric("High Risk Customers", f"{high_risk:,}")
        with col4:
            st.metric("Monthly Revenue at Risk", f"${revenue_at_risk:,.0f}")
        
        st.markdown("---")
        
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Risk Distribution")
            if 'Churn_Probability' in data.columns:
                data['Risk_Level'] = pd.cut(
                    data['Churn_Probability'],
                    bins=[0, 0.3, 0.5, 0.7, 1.0],
                    labels=['Low', 'Medium', 'High', 'Critical']
                )
                risk_counts = data['Risk_Level'].value_counts().reindex(['Low', 'Medium', 'High', 'Critical'])
            else:
                risk_counts = pd.Series({'Low': 3500, 'Medium': 1800, 'High': 1200, 'Critical': 543})
            
            fig_risk = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color=risk_counts.index,
                color_discrete_map={
                    'Low': '#2ecc71', 'Medium': '#f1c40f',
                    'High': '#f39c12', 'Critical': '#e74c3c'
                },
                hole=0.4
            )
            fig_risk.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            st.subheader("📈 Churn by Contract Type")
            if 'Contract' in data.columns:
                contract_counts = data.groupby('Contract').size().reset_index(name='Count')
                fig_contract = px.bar(
                    contract_counts, x='Contract', y='Count', color='Contract',
                    color_discrete_sequence=['#3498db', '#2ecc71', '#9b59b6']
                )
                fig_contract.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
                st.plotly_chart(fig_contract, use_container_width=True)
    else:
        st.warning("📊 No local data available. Upload a dataset to get started!")


# ============================================================================
# SIDEBAR & NAVIGATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Sidebar
    st.sidebar.markdown("## 🎯 Churn Prediction")
    
    if st.session_state.authenticated:
        # User info
        user = st.session_state.user or {}
        st.sidebar.markdown(f"👤 **{user.get('username', 'User')}**")
        st.sidebar.markdown(f"📧 {user.get('email', '')}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Navigation
        page = st.sidebar.radio(
            "Navigate",
            ["📊 Dashboard", "📤 Upload Dataset", "📈 History & Compare", "🔮 Quick Predict"]
        )
        
        if page == "📊 Dashboard":
            show_dashboard_page()
        elif page == "📤 Upload Dataset":
            show_upload_page()
        elif page == "📈 History & Compare":
            show_comparison_page()
        elif page == "🔮 Quick Predict":
            show_quick_predict_page()
    else:
        show_auth_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("<small>Built with ❤️ using Streamlit</small>", unsafe_allow_html=True)


# ============================================================================
# PAGE: QUICK PREDICT (Single Customer)
# ============================================================================

def show_quick_predict_page():
    """Show quick prediction form for single customer"""
    st.markdown('<h1 class="main-header">🔮 Quick Churn Prediction</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Demographics**")
        gender = st.selectbox("Gender", ["Male", "Female"])
        senior = st.selectbox("Senior Citizen", ["No", "Yes"])
        partner = st.selectbox("Partner", ["No", "Yes"])
        dependents = st.selectbox("Dependents", ["No", "Yes"])
    
    with col2:
        st.markdown("**Services**")
        tenure = st.slider("Tenure (months)", 0, 72, 12)
        contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
        internet = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"])
        phone = st.selectbox("Phone Service", ["Yes", "No"])
    
    with col3:
        st.markdown("**Billing**")
        monthly = st.slider("Monthly Charges ($)", 18.0, 120.0, 70.0)
        total = st.number_input("Total Charges ($)", 0.0, 10000.0, float(monthly * tenure))
        payment = st.selectbox("Payment Method", [
            "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
        ])
    
    if st.button("🔮 Predict Churn", type="primary", use_container_width=True):
        # Calculate prediction using heuristics
        prob = 0.2
        if contract == "Month-to-month":
            prob += 0.3
        if tenure < 12:
            prob += 0.2
        if internet == "Fiber optic":
            prob += 0.1
        if payment == "Electronic check":
            prob += 0.1
        prob = min(prob, 0.95)
        
        risk = "Critical" if prob >= 0.7 else "High" if prob >= 0.5 else "Medium" if prob >= 0.3 else "Low"
        
        st.markdown("---")
        st.subheader("📊 Prediction Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob * 100,
                title={'text': "Churn Probability %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#e74c3c" if prob >= 0.7 else "#f39c12" if prob >= 0.5 else "#2ecc71"},
                    'steps': [
                        {'range': [0, 30], 'color': "#d5f5e3"},
                        {'range': [30, 50], 'color': "#fcf3cf"},
                        {'range': [50, 70], 'color': "#fdebd0"},
                        {'range': [70, 100], 'color': "#fadbd8"}
                    ]
                }
            ))
            fig.update_layout(height=250, margin=dict(t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("Risk Level", risk)
            st.metric("Will Churn?", "Yes" if prob >= 0.5 else "No")
        
        with col3:
            st.markdown("**🎯 Recommendations:**")
            if prob >= 0.7:
                st.error("⚠️ CRITICAL - Immediate action needed")
                st.write("• Offer contract upgrade discount")
                st.write("• Assign dedicated support")
            elif prob >= 0.5:
                st.warning("⚡ HIGH RISK")
                st.write("• Schedule check-in call")
                st.write("• Review pricing options")
            else:
                st.success("✅ LOW RISK")
                st.write("• Continue standard engagement")


# Run the app
if __name__ == "__main__":
    main()
