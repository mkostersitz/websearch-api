# Admin Dashboard - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend

```bash
cd /Users/mikek/repos/websearch-api
./run.sh api
```

✅ Backend running at: http://localhost:8000  
📚 API Docs: http://localhost:8000/docs

### Step 2: Start the Dashboard

```bash
./start-dashboard.sh
```

Or manually:

```bash
cd admin-dashboard
npm install  # First time only
npm run dev
```

✅ Dashboard at: http://localhost:3000

### Step 3: Login

When prompted for API key, enter:

```
GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU
```

## 📊 What You Get

### Dashboard Page
- Total clients, users, and searches
- System health indicators
- Quick stats overview

### Client Management
- View all API clients
- Create/Edit/Delete clients
- Copy API keys
- Manage rate limits & quotas

### Analytics
- Search volume charts
- Provider statistics
- Top search queries
- 30-day trends

### Audit Logs
- Complete action history
- Filter by client/action/date
- Export to CSV

### System Health
- MongoDB status
- Redis connection
- Search provider health
- Auto-refresh monitoring

## 🔧 Requirements

- Node.js 18+ (`node --version`)
- npm 8+ (`npm --version`)
- Backend API running (port 8000)

## 📝 Common Commands

```bash
# Start everything
./start-all.sh          # Start OTEL + MongoDB + Redis
./run.sh api            # Start API
./start-dashboard.sh    # Start dashboard

# Stop everything
./run.sh stop           # Stop API
./stop-all.sh           # Stop infrastructure

# Development
cd admin-dashboard
npm run dev             # Dev server with hot reload
npm run build           # Production build
npm run preview         # Preview production build
```

## 🐛 Troubleshooting

**Dashboard won't connect?**
- Check backend is running: `curl http://localhost:8000/health`
- Verify API key is correct
- Check browser console for errors

**Charts not showing?**
- Make sure you have some search data
- Try the test search: `./run.sh test --pretty`
- Check Network tab in DevTools

**Build errors?**
- Run `npm install` in admin-dashboard/
- Delete `node_modules` and reinstall
- Check Node.js version (need 18+)

## 🎯 Next Steps

1. Create some test clients
2. Run sample searches
3. View analytics & trends
4. Explore audit logs
5. Monitor system health

## 📚 More Info

- Dashboard README: `admin-dashboard/README.md`
- API Documentation: http://localhost:8000/docs
- Admin UI Status: `ADMIN_UI_STATUS.md`
- Full Plan: `plan.md`

Enjoy your Enterprise Admin Dashboard! 🎉
