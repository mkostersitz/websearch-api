# WebSearch API - Admin Dashboard

Enterprise admin dashboard for managing and monitoring the WebSearch API.

## Quick Start

### 1. Start the Backend

The dashboard requires the WebSearch API backend to be running:

```bash
cd /Users/mikek/repos/websearch-api
./run.sh api
```

Backend will be available at: http://localhost:8000

### 2. Start the Dashboard

From the repository root:

```bash
./start-dashboard.sh
```

Or manually:

```bash
cd admin-dashboard
npm install  # First time only
npm run dev
```

Dashboard will be available at: http://localhost:3000

### 3. Login

When prompted, enter the admin API key:
```
GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU
```

The key will be stored in your browser's localStorage for future sessions.

## Features

### Dashboard
- Overview statistics (total clients, searches, active clients)
- 7-day search trends chart with interactive visualization
- Real-time system health indicators
- Search provider status monitoring
- Responsive cards with color-coded metrics

### Client Management
- DataGrid view with sorting and filtering
- Create new clients with custom rate limits and quotas
- Edit existing client configurations
- Delete clients (with confirmation)
- Copy API keys to clipboard with one click
- Active/inactive status toggle
- Pagination for large datasets

### Analytics
- Search volume trends with selectable time ranges (7/30/90 days)
- Interactive line charts showing daily search patterns
- Pie chart breakdown of searches by provider
- Top search queries table with rankings
- Color-coded provider statistics
- Total search count display

### Audit Logs
- Complete audit trail of all API actions
- Advanced filtering by client ID, action, date range
- Expandable rows showing full JSON event details
- Export to CSV functionality
- Color-coded action badges (CREATE/UPDATE/DELETE)
- Pagination and search
- IP address and user agent tracking

### System Health
- Real-time database connection monitoring
- Redis cache status indicators
- Search provider health checks with response times
- Auto-refresh every 30 seconds (toggleable)
- Color-coded status badges (green/red)
- Last updated timestamp
- Connection details table

## Tech Stack

- **React** 18.2 - UI framework
- **TypeScript** 5.3 - Type safety
- **Material-UI** 5.14 - Component library
- **Recharts** 2.10 - Data visualization
- **Axios** - HTTP client
- **React Router** 6.20 - Navigation
- **Vite** 5.0 - Build tool & dev server

## Development

### Available Scripts

```bash
npm run dev      # Start development server (port 3000)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run TypeScript linter
```

### Project Structure

```
admin-dashboard/
├── src/
│   ├── components/       # Reusable UI components
│   │   └── ApiKeyPrompt.tsx
│   ├── pages/           # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Clients.tsx
│   │   ├── Analytics.tsx
│   │   ├── AuditLogs.tsx
│   │   └── SystemHealth.tsx
│   ├── services/        # API client
│   │   └── api.ts
│   ├── types/           # TypeScript types
│   │   └── index.ts
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### API Integration

The dashboard communicates with the backend API at `http://localhost:8000`.

All requests include the `X-API-Key` header for authentication.

API proxy is configured in `vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

### Adding New Features

1. **Add a new page:**
   - Create component in `src/pages/`
   - Add route in `src/App.tsx`
   - Add nav item to sidebar

2. **Add API endpoint:**
   - Add method in `src/services/api.ts`
   - Define types in `src/types/index.ts`
   - Use in component with error handling

3. **Add new chart:**
   - Import from `recharts`
   - Fetch data using API service
   - Handle loading and error states

## Production Build

To build for production:

```bash
npm run build
```

Output will be in `dist/` directory.

Serve with any static file server:

```bash
npm run preview
```

Or deploy to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Nginx
- Apache

## Configuration

Environment variables can be set in `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_VERSION=v1
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Troubleshooting

### Dashboard won't load
- Check backend is running: `curl http://localhost:8000/health`
- Check browser console for errors
- Verify CORS is configured in backend `.env`

### API requests failing
- Verify admin API key is correct
- Check Network tab in browser DevTools
- Ensure backend is accessible at port 8000

### Charts not rendering
- Check data format matches expected structure
- Verify recharts is installed: `npm list recharts`
- Check browser console for errors

### TypeScript errors
- Run `npm install` to ensure dependencies are installed
- Check `tsconfig.json` configuration
- Restart VS Code TypeScript server

## Support

- Backend API docs: http://localhost:8000/docs
- Jaeger traces: http://localhost:17686
- Grafana dashboards: http://localhost:3002
