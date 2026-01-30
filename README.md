# 🎨 Churn Prediction Dashboard

React + Tailwind CSS frontend for customer churn analytics.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── KpiCard.jsx
│   │   │   ├── RiskChart.jsx
│   │   │   └── SegmentChart.jsx
│   │   ├── Customers/
│   │   │   ├── CustomerTable.jsx
│   │   │   ├── CustomerDetail.jsx
│   │   │   └── Filters.jsx
│   │   ├── Explainability/
│   │   │   ├── ShapChart.jsx
│   │   │   └── FeatureImpact.jsx
│   │   ├── Retention/
│   │   │   ├── ActionList.jsx
│   │   │   └── PriorityBadge.jsx
│   │   └── Layout/
│   │       ├── Sidebar.jsx
│   │       ├── Topbar.jsx
│   │       └── MainLayout.jsx
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Customers.jsx
│   │   ├── Retention.jsx
│   │   └── Settings.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   └── main.jsx
├── public/
├── index.html
├── package.json
├── tailwind.config.js
└── vite.config.js
```

## 🛠️ Tech Stack

- React 18
- Vite
- Tailwind CSS
- Recharts (charts)
- Axios (API calls)
- React Router

## 🔧 Environment Variables

Create a `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

## 📜 License

MIT License
