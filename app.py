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
# Persist the uploaded DataFrame so it survives page switches
if 'uploaded_df' not in st.session_state:
    st.session_state.uploaded_df = None
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None
# Store all uploaded datasets for history & comparison (list of dicts)
if 'dataset_history' not in st.session_state:
    st.session_state.dataset_history = []
# Store DataFrames uploaded specifically for comparison
if 'comparison_datasets' not in st.session_state:
    st.session_state.comparison_datasets = {}


# ============================================================================
# LOCAL ANALYSIS HELPERS
# ============================================================================

def analyze_dataframe(df, filename="dataset"):
    """Perform churn analysis locally on a DataFrame.
    Works whether the data already has Churn_Probability or not.
    Returns a dict similar to the API response.
    """
    total_customers = len(df)

    # --- Churn probability ---------------------------------------------------
    if 'Churn_Probability' in df.columns:
        churn_prob = df['Churn_Probability']
    elif 'Churn' in df.columns:
        # Derive a simple probability from actual churn label
        churn_prob = df['Churn'].map({'Yes': 0.85, 'No': 0.15, 1: 0.85, 0: 0.15}).fillna(0.5)
    else:
        churn_prob = pd.Series([0.5] * total_customers)

    churn_rate = float(churn_prob.mean() * 100)
    high_risk_count = int((churn_prob >= 0.7).sum())

    # Revenue at risk
    if 'MonthlyCharges' in df.columns:
        revenue_at_risk = float(df.loc[churn_prob >= 0.5, 'MonthlyCharges'].sum())
        total_revenue = float(df['MonthlyCharges'].sum())
    else:
        revenue_at_risk = 0.0
        total_revenue = 0.0

    # Segment stats
    bins = [0, 0.3, 0.5, 0.7, 1.01]
    labels = ['Low', 'Medium', 'High', 'Critical']
    risk_levels = pd.cut(churn_prob, bins=bins, labels=labels, include_lowest=True)
    segment_stats = {}
    for level in labels:
        mask = risk_levels == level
        count = int(mask.sum())
        rev = float(df.loc[mask, 'MonthlyCharges'].sum()) if 'MonthlyCharges' in df.columns else 0
        segment_stats[level] = {'count': count, 'revenue': rev}

    return {
        'filename': filename,
        'total_customers': total_customers,
        'churn_rate': churn_rate,
        'high_risk_count': high_risk_count,
        'revenue_at_risk': revenue_at_risk,
        'total_revenue': total_revenue,
        'segment_stats': segment_stats,
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }


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
    return api_request("POST", "/dataset/upload", data=data, files=files)


def get_dataset_history(limit=10):
    """Get user's dataset upload history"""
    return api_request("GET", f"/dataset/?page=1&page_size={limit}")


def compare_datasets_api(dataset_1_id, dataset_2_id):
    """Compare two specific datasets via backend API"""
    data = {"dataset_1_id": dataset_1_id, "dataset_2_id": dataset_2_id}
    return api_request("POST", "/dataset/compare", data)


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
    1. **Analyze** your dataset locally
    2. **Predict** churn probability for each customer
    3. **Store** results for future comparison across pages
    4. **Compare** with other uploads to track progress
    """)
    
    st.markdown("---")
    
    # File Upload Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Customer CSV",
            type=["csv"],
            help="Upload a CSV file with customer data",
            key="upload_page_file"
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
            
            if st.button("🚀 Analyze Dataset", type="primary", use_container_width=True):
                with st.spinner("Analyzing dataset..."):
                    # ----- LOCAL analysis (always works) -----
                    analysis = analyze_dataframe(df_preview, filename=uploaded_file.name)

                    # Persist the DataFrame & analysis in session state
                    st.session_state.uploaded_df = df_preview
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.current_analysis = analysis

                    # Also add to history for the comparison page
                    st.session_state.dataset_history.append({
                        **analysis,
                        'df': df_preview,
                    })

                st.success("✅ Dataset analyzed successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

    # --- Still show the PREVIOUS analysis when file uploader is empty --------
    elif st.session_state.uploaded_df is not None:
        st.markdown("### 📋 Previously Loaded Data")
        st.dataframe(st.session_state.uploaded_df.head(10), use_container_width=True)
        st.info(
            f"📊 Total rows: {len(st.session_state.uploaded_df):,} | "
            f"Columns: {len(st.session_state.uploaded_df.columns)} | "
            f"File: {st.session_state.uploaded_filename}"
        )
    
    # Show Current Analysis Results
    if st.session_state.current_analysis:
        _render_analysis_results(st.session_state.current_analysis)


def _render_analysis_results(analysis):
    """Reusable widget to render analysis KPIs + charts."""
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
# PAGE: HISTORY & COMPARISON  (local multi-file upload)
# ============================================================================

def show_comparison_page():
    """Show dataset comparison with multi-file upload support."""
    st.markdown('<h1 class="main-header">📈 Dataset Comparison</h1>', unsafe_allow_html=True)

    st.markdown("""
    Upload **two or more** CSV files to compare churn metrics side-by-side.
    You can also re-use any dataset you already analyzed on the Upload page.
    """)

    st.markdown("---")

    # ----- Multi-file uploader ------------------------------------------------
    comparison_files = st.file_uploader(
        "Upload CSV files for comparison",
        type=["csv"],
        accept_multiple_files=True,
        help="Select two or more customer CSV files to compare",
        key="comparison_uploader",
    )

    if comparison_files:
        new_datasets = {}
        for f in comparison_files:
            try:
                df = pd.read_csv(f)
                new_datasets[f.name] = df
            except Exception as e:
                st.error(f"❌ Error reading {f.name}: {e}")

        if new_datasets:
            st.session_state.comparison_datasets = new_datasets
            st.success(f"✅ Loaded {len(new_datasets)} dataset(s)")

    # Also include datasets from the Upload page history
    for item in st.session_state.dataset_history:
        name = item.get('filename', 'unknown')
        if name not in st.session_state.comparison_datasets and 'df' in item:
            st.session_state.comparison_datasets[name] = item['df']

    datasets = st.session_state.comparison_datasets

    if not datasets:
        st.info("📭 No datasets available yet.  Upload files above or analyze a dataset on the **Upload** page first.")
        return

    # ----- Show loaded dataset names ------------------------------------------
    st.markdown("### 📂 Loaded Datasets")
    for name, df in datasets.items():
        st.write(f"- **{name}** — {len(df):,} rows, {len(df.columns)} columns")

    st.markdown("---")

    if len(datasets) < 2:
        st.warning("⚠️ Upload at least **2 datasets** to enable comparison.")
        # Still show single-dataset analysis
        name, df = list(datasets.items())[0]
        st.markdown(f"### 📊 Analysis: {name}")
        _render_analysis_results(analyze_dataframe(df, name))
        return

    # ----- Let user choose which two to compare ------------------------------
    dataset_names = list(datasets.keys())

    col1, col2 = st.columns(2)
    with col1:
        baseline_name = st.selectbox(
            "Baseline Dataset (older / reference)",
            options=dataset_names,
            index=0,
            key="cmp_baseline",
        )
    with col2:
        current_name = st.selectbox(
            "Current Dataset (newer)",
            options=dataset_names,
            index=min(1, len(dataset_names) - 1),
            key="cmp_current",
        )

    if baseline_name == current_name:
        st.warning("Please select **different** datasets for comparison.")
        return

    if st.button("📊 Compare Datasets", type="primary", use_container_width=True):
        with st.spinner("Comparing…"):
            a1 = analyze_dataframe(datasets[baseline_name], baseline_name)
            a2 = analyze_dataframe(datasets[current_name], current_name)
            comparison = _build_local_comparison(a1, a2)
        show_comparison_results(comparison)

    # ----- Overview table of ALL loaded datasets ------------------------------
    st.markdown("---")
    st.markdown("### 📊 All Datasets Overview")
    overview_rows = []
    for name, df in datasets.items():
        a = analyze_dataframe(df, name)
        overview_rows.append({
            'Dataset': a['filename'],
            'Customers': a['total_customers'],
            'Churn Rate %': round(a['churn_rate'], 1),
            'High Risk': a['high_risk_count'],
            'Revenue at Risk ($)': round(a['revenue_at_risk'], 0),
        })
    st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)


def _build_local_comparison(a1, a2):
    """Build a comparison dict from two local analysis dicts."""
    churn_change = a2['churn_rate'] - a1['churn_rate']
    customer_change = a2['total_customers'] - a1['total_customers']
    revenue_change = a2.get('total_revenue', 0) - a1.get('total_revenue', 0)
    risk_change = a2['revenue_at_risk'] - a1['revenue_at_risk']
    is_improvement = churn_change < 0
    # Rough annualised P/L: saved revenue if churn drops, lost revenue otherwise
    profit_loss = -risk_change * 12 if is_improvement else risk_change * 12

    return {
        'dataset_1_filename': a1['filename'],
        'dataset_2_filename': a2['filename'],
        'is_improvement': is_improvement,
        'profit_loss_amount': abs(profit_loss) if is_improvement else -abs(profit_loss),
        'customer_change': customer_change,
        'churn_rate_change': churn_change,
        'revenue_change': revenue_change,
        'risk_change': risk_change,
        'detailed_comparison': {
            'period_1': {
                'customers': a1['total_customers'],
                'revenue': a1.get('total_revenue', 0),
                'churn_rate': a1['churn_rate'],
                'revenue_at_risk': a1['revenue_at_risk'],
            },
            'period_2': {
                'customers': a2['total_customers'],
                'revenue': a2.get('total_revenue', 0),
                'churn_rate': a2['churn_rate'],
                'revenue_at_risk': a2['revenue_at_risk'],
            },
            'insights': _generate_insights(a1, a2),
        }
    }


def _generate_insights(a1, a2):
    """Generate human-readable comparison insights."""
    insights = []
    churn_diff = a2['churn_rate'] - a1['churn_rate']
    if churn_diff < -5:
        insights.append(f"Churn rate dropped significantly by {abs(churn_diff):.1f} pp – great progress!")
    elif churn_diff < 0:
        insights.append(f"Churn rate improved by {abs(churn_diff):.1f} pp.")
    elif churn_diff > 5:
        insights.append(f"Churn rate increased sharply by {churn_diff:.1f} pp – investigate root causes.")
    elif churn_diff > 0:
        insights.append(f"Churn rate rose slightly by {churn_diff:.1f} pp.")
    else:
        insights.append("Churn rate is unchanged.")

    cust_diff = a2['total_customers'] - a1['total_customers']
    if cust_diff > 0:
        insights.append(f"Customer base grew by {cust_diff:,}.")
    elif cust_diff < 0:
        insights.append(f"Customer base shrank by {abs(cust_diff):,}.")

    risk_diff = a2['revenue_at_risk'] - a1['revenue_at_risk']
    if risk_diff < 0:
        insights.append(f"Revenue at risk decreased by ${abs(risk_diff):,.0f} – retention is working.")
    elif risk_diff > 0:
        insights.append(f"Revenue at risk increased by ${risk_diff:,.0f} – consider targeted campaigns.")

    return insights


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

def _load_default_data():
    """Load default customer predictions CSV if it exists."""
    try:
        if PREDICTIONS_FILE.exists():
            return pd.read_csv(PREDICTIONS_FILE)
    except Exception:
        pass
    return None


def show_dashboard_page():
    """Show main dashboard – uses uploaded data first, falls back to default CSV."""
    st.markdown('<h1 class="main-header">📊 Customer Churn Dashboard</h1>', unsafe_allow_html=True)

    # ---- Inline uploader so users can load data directly on the dashboard ----
    with st.expander("📂 Upload a dataset to analyse", expanded=(st.session_state.uploaded_df is None)):
        dash_file = st.file_uploader(
            "Drop a CSV here to view its dashboard",
            type=["csv"],
            key="dashboard_file_uploader",
        )
        if dash_file is not None:
            try:
                df_new = pd.read_csv(dash_file)
                st.session_state.uploaded_df = df_new
                st.session_state.uploaded_filename = dash_file.name
                # Run local analysis and store it
                analysis = analyze_dataframe(df_new, filename=dash_file.name)
                st.session_state.current_analysis = analysis
                st.session_state.dataset_history.append({**analysis, "df": df_new})
                st.success(f"✅ Loaded **{dash_file.name}** ({len(df_new):,} rows)")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not read file: {e}")

    # Determine which DataFrame to display
    if st.session_state.uploaded_df is not None:
        data = st.session_state.uploaded_df
        source_label = f"Uploaded: {st.session_state.uploaded_filename}"
    else:
        data = _load_default_data()
        source_label = "Default sample data"

    if data is None or data.empty:
        st.info("📊 No data loaded yet. Use the uploader above or go to **Upload Dataset** to load a CSV file.")
        return

    st.caption(f"📁 Data source: **{source_label}** ({len(data):,} rows)")

    # --- KPI Metrics Row ---
    col1, col2, col3, col4 = st.columns(4)
    total_customers = len(data)

    if 'Churn_Probability' in data.columns:
        churn_prob = data['Churn_Probability']
    elif 'Churn' in data.columns:
        churn_prob = data['Churn'].map({'Yes': 0.85, 'No': 0.15, 1: 0.85, 0: 0.15}).fillna(0.5)
    else:
        churn_prob = pd.Series([0.5] * total_customers)

    high_risk = int((churn_prob >= 0.7).sum())
    critical_risk = int((churn_prob >= 0.5).sum())
    revenue_at_risk = float(data.loc[churn_prob >= 0.5, 'MonthlyCharges'].sum()) if 'MonthlyCharges' in data.columns else 0
    churn_rate = float(churn_prob.mean() * 100)

    with col1:
        st.metric("Total Customers", f"{total_customers:,}")
    with col2:
        st.metric("Avg Churn Risk", f"{churn_rate:.1f}%")
    with col3:
        st.metric("High Risk Customers", f"{high_risk:,}")
    with col4:
        st.metric("Monthly Revenue at Risk", f"${revenue_at_risk:,.0f}")

    st.markdown("---")

    # --- Charts Row ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Risk Distribution")
        risk_levels = pd.cut(
            churn_prob,
            bins=[0, 0.3, 0.5, 0.7, 1.01],
            labels=['Low', 'Medium', 'High', 'Critical'],
            include_lowest=True,
        )
        risk_counts = risk_levels.value_counts().reindex(['Low', 'Medium', 'High', 'Critical']).fillna(0)

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
            st.info("Contract column not found in dataset.")

    # --- Additional analytics charts ---
    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("💰 Monthly Charges Distribution")
        if 'MonthlyCharges' in data.columns:
            fig_charges = px.histogram(
                data, x='MonthlyCharges', nbins=30,
                color_discrete_sequence=['#1f77b4'],
                labels={'MonthlyCharges': 'Monthly Charges ($)'},
            )
            fig_charges.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_charges, use_container_width=True)

    with col4:
        st.subheader("📅 Tenure Distribution")
        if 'Tenure' in data.columns:
            fig_tenure = px.histogram(
                data, x='Tenure', nbins=20,
                color_discrete_sequence=['#9b59b6'],
                labels={'Tenure': 'Tenure (months)'},
            )
            fig_tenure.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_tenure, use_container_width=True)

    # --- Data table ---
    st.markdown("---")
    st.subheader("🔍 Customer Data Preview")
    st.dataframe(data.head(50), use_container_width=True)


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
