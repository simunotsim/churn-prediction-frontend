# 📊 Customer Churn Prediction Dashboard

Interactive Streamlit dashboard with user authentication, dynamic dataset upload, and profit/loss comparison analytics.

## ✨ Key Features

- 🔐 **User Authentication** - Register/Login with secure JWT tokens
- 📤 **Dynamic Dataset Upload** - Upload your own CSV for instant analysis
- 📈 **Dataset Comparison** - Compare datasets over time with profit/loss insights
- 📊 **Interactive Dashboard** - Real-time KPIs and visualizations
- 🔮 **Live Predictions** - Predict churn for individual customers
- 🎯 **Retention Actions** - Priority-based action recommendations
- 📉 **Model Performance** - View model metrics and feature importance

## 🚀 Quick Start

```powershell
# Install dependencies
cd frontend
pip install -r requirements.txt

# Set environment (optional)
cp .env.example .env

# Run dashboard
streamlit run app.py
```

Dashboard opens at: **http://localhost:8501**

> ⚠️ Make sure the backend API is running at `http://localhost:8000`

## 📱 Pages

### 🔐 Login / Register
- Create new account with email, username, password
- Company and full name (optional)
- Secure session management
- Automatic token refresh

### 📤 Upload Dataset
- Drag & drop CSV file upload
- Instant ML analysis
- View predictions summary:
  - Total customers
  - Churn rate
  - Revenue at risk
  - Risk distribution chart
- Results saved to database

### 📊 Dashboard
- **KPI Cards**: Total customers, churn rate, high-risk count, revenue at risk
- **Risk Distribution**: Pie chart (Low/Medium/High/Critical)
- **Contract Analysis**: Bar chart by contract type
- **Customer Segments**: 4-quadrant segmentation
- **Churn Distribution**: Histogram of probabilities

### 👥 Customers
- **Search**: Find customers by ID
- **Filter**: By risk level, contract type
- **View**: Customer details with predictions
- **Paginated**: Handle large datasets

### 🔮 Predict Churn
- **Input Form**: Enter customer attributes
- **Demographics**: Gender, senior citizen, partner, dependents
- **Services**: Contract, internet, phone, tech support
- **Billing**: Monthly charges, payment method
- **Results**: Churn probability gauge, risk level, recommendations

### 📜 Dataset History & Comparison
- **History Table**: All uploaded datasets with stats
- **Select & Compare**: Pick two datasets
- **Profit/Loss Analysis**:
  - Customer count change
  - Churn rate change
  - Revenue change
  - Risk change
  - **Annual profit/loss estimate**
- **Status**: Improved ✅ / Declined ❌ / Stable ➡️

### 🎯 Retention Actions
- **Priority Levels**: Critical, High, Medium
- **Customer List**: With churn probability
- **Strategies**: Personalized recommendations
- **Export**: Download as CSV

### 📈 Model Performance
- **Best Model**: Highlighted with ROC-AUC score
- **Comparison Table**: All trained models
- **Charts**: ROC-AUC comparison
- **Feature Importance**: Top contributing features

## 🔄 User Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Register  │ ──► │    Login    │ ──► │  Dashboard  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
            │   Upload    │           │  Customers  │           │   Predict   │
            │   Dataset   │           │   Explorer  │           │   Churn     │
            └─────────────┘           └─────────────┘           └─────────────┘
                    │
                    ▼
            ┌─────────────┐           ┌─────────────┐
            │   History   │ ──────►   │   Compare   │
            │   View      │           │   Datasets  │
            └─────────────┘           └─────────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │ Profit/Loss │
                                    │   Report    │
                                    └─────────────┘
```

## 📊 Dataset Comparison Metrics

| Metric | Calculation | Meaning |
|--------|-------------|---------|
| Customer Change | Dataset2 - Dataset1 customers | Growth or decline |
| Churn Rate Change | Dataset2 - Dataset1 churn % | Improvement if negative |
| Revenue Change | Dataset2 - Dataset1 revenue | Financial growth |
| Risk Change | Dataset2 - Dataset1 at-risk revenue | Lower is better |
| Profit/Loss | (Risk Change × 12) + (Revenue Change × 12) | Annual impact estimate |

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Streamlit |
| Charts | Plotly |
| Data | Pandas, NumPy |
| HTTP | Requests |
| State | Streamlit Session State |

## 📁 Project Structure

```
frontend/
├── app.py              # Main Streamlit application
│   ├── Login/Register  # Authentication pages
│   ├── Upload Dataset  # CSV upload & analysis
│   ├── Dashboard       # KPI visualizations
│   ├── Customers       # Customer explorer
│   ├── Predict Churn   # Prediction form
│   ├── History         # Dataset history & comparison
│   ├── Retention       # Retention actions
│   └── Model Info      # Model performance
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_ROOT` | Auto-detected | Project root path |
| `DATA_PATH` | `../data/processed` | Path to data files |
| `API_URL` | `http://localhost:8000` | Backend API URL |

## 🔌 API Integration

The dashboard communicates with the FastAPI backend for:

| Feature | Endpoint | Method |
|---------|----------|--------|
| Register | `/auth/register` | POST |
| Login | `/auth/login-json` | POST |
| User Info | `/auth/me` | GET |
| Upload Dataset | `/datasets/upload` | POST |
| Get History | `/datasets/history` | GET |
| Compare | `/datasets/compare` | POST |
| Predict | `/predict` | POST |
| Customers | `/customers` | GET |
| Retention | `/retention/actions` | GET |
| Model Metrics | `/model/metrics` | GET |

## 🎨 UI Components

### Custom Styling
- Color-coded risk levels (Green/Yellow/Orange/Red)
- Responsive layout
- Dark-mode compatible charts
- Metric cards with deltas

### Interactive Elements
- File uploader with drag & drop
- Dropdown filters
- Search inputs
- Date pickers
- Download buttons

## 📋 CSV Format Requirements

For dataset upload, your CSV should include these columns:

| Column | Type | Required |
|--------|------|----------|
| CustomerID | String | ✅ |
| Gender | Male/Female | ✅ |
| SeniorCitizen | 0/1 | ✅ |
| Partner | Yes/No | ✅ |
| Dependents | Yes/No | ✅ |
| Tenure | Integer | ✅ |
| PhoneService | Yes/No | ✅ |
| InternetService | DSL/Fiber optic/No | ✅ |
| Contract | Month-to-month/One year/Two year | ✅ |
| PaperlessBilling | Yes/No | ✅ |
| PaymentMethod | String | ✅ |
| MonthlyCharges | Float | ✅ |
| TotalCharges | Float | ✅ |

## 🧪 Testing

1. Start backend: `cd backend/api && python main.py`
2. Start frontend: `cd frontend && streamlit run app.py`
3. Register a new account
4. Upload a test dataset
5. Explore dashboard features
6. Upload another dataset and compare

## 📜 License

MIT License
