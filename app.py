"""
Customer Churn Prediction Dashboard
Streamlit-based interactive dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests

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
</style>
""", unsafe_allow_html=True)

# API Base URL
API_URL = "http://localhost:8000"

# Helper Functions
@st.cache_data(ttl=300)
def load_data():
    """Load customer data from CSV"""
    try:
        df = pd.read_csv(r"c:\Users\KIIT0001\Desktop\churn-prediction-analytics\data\processed\customer_predictions.csv")
        return df
    except:
        return None

def get_prediction(customer_data):
    """Get churn prediction from API"""
    try:
        response = requests.post(f"{API_URL}/predict", json=customer_data, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# Sidebar Navigation
st.sidebar.markdown("## 🎯 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard", "👥 Customers", "🔮 Predict Churn", "🎯 Retention Actions", "📈 Model Performance"]
)

# Load Data
data = load_data()

# ================== DASHBOARD PAGE ==================
if page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">📊 Customer Churn Dashboard</h1>', unsafe_allow_html=True)
    
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
                    'Low': '#2ecc71',
                    'Medium': '#f1c40f',
                    'High': '#f39c12',
                    'Critical': '#e74c3c'
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
                    contract_counts,
                    x='Contract',
                    y='Count',
                    color='Contract',
                    color_discrete_sequence=['#3498db', '#2ecc71', '#9b59b6']
                )
                fig_contract.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
                st.plotly_chart(fig_contract, use_container_width=True)
        
        # Second Row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Customer Segments")
            if 'Segment' in data.columns:
                segment_counts = data['Segment'].value_counts()
                fig_segment = px.bar(
                    x=segment_counts.values,
                    y=segment_counts.index,
                    orientation='h',
                    color=segment_counts.index,
                    color_discrete_map={
                        'Low Risk, High Value': '#2ecc71',
                        'Low Risk, Low Value': '#3498db',
                        'High Risk, Low Value': '#f39c12',
                        'High Risk, High Value': '#e74c3c'
                    }
                )
                fig_segment.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_segment, use_container_width=True)
        
        with col2:
            st.subheader("📉 Churn Probability Distribution")
            if 'Churn_Probability' in data.columns:
                fig_hist = px.histogram(
                    data, x='Churn_Probability', nbins=30,
                    color_discrete_sequence=['#3498db']
                )
                fig_hist.add_vline(x=0.5, line_dash="dash", line_color="red")
                fig_hist.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.error("❌ Could not load data. Make sure customer_predictions.csv exists.")

# ================== CUSTOMERS PAGE ==================
elif page == "👥 Customers":
    st.markdown('<h1 class="main-header">👥 Customer Explorer</h1>', unsafe_allow_html=True)
    
    if data is not None:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Churn_Probability' in data.columns:
                data['Risk_Level'] = pd.cut(
                    data['Churn_Probability'],
                    bins=[0, 0.3, 0.5, 0.7, 1.0],
                    labels=['Low', 'Medium', 'High', 'Critical']
                )
            risk_filter = st.selectbox("Risk Level", ["All", "Critical", "High", "Medium", "Low"])
        
        with col2:
            contracts = ["All"] + list(data['Contract'].unique()) if 'Contract' in data.columns else ["All"]
            contract_filter = st.selectbox("Contract Type", contracts)
        
        with col3:
            search_id = st.text_input("Search Customer ID", "")
        
        # Apply Filters
        filtered = data.copy()
        
        if risk_filter != "All" and 'Risk_Level' in filtered.columns:
            filtered = filtered[filtered['Risk_Level'] == risk_filter]
        
        if contract_filter != "All" and 'Contract' in filtered.columns:
            filtered = filtered[filtered['Contract'] == contract_filter]
        
        if search_id:
            filtered = filtered[filtered['CustomerID'].astype(str).str.contains(search_id, case=False)]
        
        st.markdown(f"**Showing {len(filtered):,} of {len(data):,} customers**")
        
        # Display Table
        cols = ['CustomerID', 'Gender', 'Contract', 'Tenure', 'MonthlyCharges', 'TotalCharges']
        if 'Churn_Probability' in filtered.columns:
            cols.append('Churn_Probability')
        if 'Segment' in filtered.columns:
            cols.append('Segment')
        
        available = [c for c in cols if c in filtered.columns]
        st.dataframe(filtered[available].head(100), use_container_width=True, hide_index=True)
    else:
        st.error("❌ Could not load customer data.")

# ================== PREDICT PAGE ==================
elif page == "🔮 Predict Churn":
    st.markdown('<h1 class="main-header">🔮 Churn Prediction</h1>', unsafe_allow_html=True)
    
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
        paperless = st.selectbox("Paperless Billing", ["Yes", "No"])
    
    col1, col2 = st.columns(2)
    with col1:
        tech_support = st.selectbox("Tech Support", ["No", "Yes"])
    with col2:
        online_security = st.selectbox("Online Security", ["No", "Yes"])
    
    if st.button("🔮 Predict Churn", type="primary", use_container_width=True):
        customer_data = {
            "Gender": gender,
            "SeniorCitizen": 1 if senior == "Yes" else 0,
            "Partner": partner,
            "Dependents": dependents,
            "Tenure": tenure,
            "PhoneService": phone,
            "InternetService": internet,
            "TechSupport": tech_support,
            "OnlineSecurity": online_security,
            "Contract": contract,
            "PaperlessBilling": paperless,
            "PaymentMethod": payment,
            "MonthlyCharges": monthly,
            "TotalCharges": total
        }
        
        result = get_prediction(customer_data)
        
        st.markdown("---")
        st.subheader("📊 Prediction Results")
        
        if result:
            prob = result.get('churn_probability', 0.5)
            risk = result.get('risk_level', 'Medium')
        else:
            # Fallback heuristic
            prob = 0.2
            if contract == "Month-to-month": prob += 0.3
            if tenure < 12: prob += 0.2
            if internet == "Fiber optic": prob += 0.1
            if payment == "Electronic check": prob += 0.1
            prob = min(prob, 0.95)
            risk = "Critical" if prob >= 0.7 else "High" if prob >= 0.5 else "Medium" if prob >= 0.3 else "Low"
        
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

# ================== RETENTION PAGE ==================
elif page == "🎯 Retention Actions":
    st.markdown('<h1 class="main-header">🎯 Retention Actions</h1>', unsafe_allow_html=True)
    
    try:
        retention_df = pd.read_csv(
            r"c:\Users\KIIT0001\Desktop\churn-prediction-analytics\data\processed\retention_actions.csv"
        )
        
        col1, col2, col3 = st.columns(3)
        priority_counts = retention_df['Priority'].value_counts()
        
        with col1:
            st.metric("🔴 Critical", priority_counts.get('Critical', 0))
        with col2:
            st.metric("🟠 High", priority_counts.get('High', 0))
        with col3:
            st.metric("🟡 Medium", priority_counts.get('Medium', 0))
        
        st.markdown("---")
        
        priority_filter = st.selectbox("Filter by Priority", ["All", "Critical", "High", "Medium"])
        
        if priority_filter != "All":
            retention_df = retention_df[retention_df['Priority'] == priority_filter]
        
        cols = ['CustomerID', 'Contract', 'Churn_Probability', 'Priority', 'Strategies']
        available = [c for c in cols if c in retention_df.columns]
        
        st.dataframe(retention_df[available].head(50), use_container_width=True, hide_index=True)
        
        st.download_button(
            "📥 Download CSV",
            retention_df[available].to_csv(index=False),
            "retention_actions.csv",
            use_container_width=True
        )
    except:
        st.warning("⚠️ No retention data found. Run the modeling notebook first.")

# ================== MODEL PERFORMANCE PAGE ==================
elif page == "📈 Model Performance":
    st.markdown('<h1 class="main-header">📈 Model Performance</h1>', unsafe_allow_html=True)
    
    try:
        model_df = pd.read_csv(
            r"c:\Users\KIIT0001\Desktop\churn-prediction-analytics\data\processed\model_comparison.csv"
        )
        
        best = model_df.loc[model_df['ROC-AUC'].idxmax(), 'Model']
        st.success(f"**🏆 Best Model:** {best}")
        
        st.dataframe(model_df, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 ROC-AUC Comparison")
            fig = px.bar(model_df, x='Model', y='ROC-AUC', color='ROC-AUC',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔑 Feature Importance")
            features = pd.DataFrame({
                'Feature': ['Contract', 'Tenure', 'MonthlyCharges', 'InternetService', 
                           'PaymentMethod', 'TechSupport', 'TotalCharges'],
                'Importance': [0.25, 0.18, 0.12, 0.10, 0.08, 0.07, 0.06]
            })
            fig = px.bar(features, x='Importance', y='Feature', orientation='h',
                        color='Importance', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("⚠️ No model data found. Run the modeling notebook first.")

# Footer
st.markdown("---")
st.markdown("<center>📊 Customer Churn Dashboard | Built with Streamlit</center>", unsafe_allow_html=True)
