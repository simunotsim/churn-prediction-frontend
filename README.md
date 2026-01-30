# 📊 Customer Churn Prediction Dashboard

Streamlit-based interactive dashboard for customer churn analytics.

## 🚀 Quick Start

```powershell
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Dashboard opens at: **http://localhost:8501**

## 📱 Features

| Page | Description |
|------|-------------|
| 📊 Dashboard | KPIs, risk charts, customer segments |
| 👥 Customers | Search, filter, view customer details |
| 🔮 Predict Churn | Input form with live prediction |
| 🎯 Retention Actions | Priority-based action list |
| 📈 Model Performance | Model comparison & feature importance |

## 📁 Project Structure

```
frontend/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🛠️ Tech Stack

- Streamlit
- Pandas
- Plotly
- Requests (API calls)

## 🔌 API Integration

The dashboard connects to the FastAPI backend at `http://localhost:8000`.
Start the backend first for full functionality:

```powershell
cd ../backend/api
uvicorn main:app --reload --port 8000
```

## 📜 License

MIT License
