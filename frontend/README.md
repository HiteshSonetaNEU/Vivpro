# Clinical Trials Search - Frontend

Modern, AI-powered clinical trials search interface built with React, TypeScript, Vite, and Tailwind CSS.

## Features

✨ **AI-Powered Search** - Natural language queries with intelligent entity extraction  
🚀 **Lightning Fast** - Optimized with caching, delivers results in milliseconds  
📱 **Responsive Design** - Beautiful UI that works on all devices  
🎨 **Modern UI/UX** - Smooth animations, intuitive navigation  
🔍 **Advanced Pagination** - Easy navigation through thousands of results  
📊 **Detailed Views** - Comprehensive trial information in modal dialogs  

## Tech Stack

- **React 18** - Modern UI library
- **TypeScript** - Type-safe development
- **Vite** - Ultra-fast build tool
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icon library

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:5000`

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open browser to `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── SearchBar.tsx    # Search input with AI indicator
│   │   ├── ResultsList.tsx  # Results grid with pagination
│   │   ├── TrialCard.tsx    # Individual trial card
│   │   ├── TrialDetailModal.tsx  # Full trial details
│   │   ├── Pagination.tsx   # Page navigation
│   │   ├── LoadingSpinner.tsx
│   │   └── EmptyState.tsx
│   ├── services/
│   │   └── api.ts           # API integration
│   ├── types/
│   │   └── trial.ts         # TypeScript interfaces
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # React entry point
│   └── index.css            # Global styles + Tailwind
├── public/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Key Features Implementation

### Natural Language Search
- Clean, prominent search bar
- Real-time loading states
- AI-powered indicator
- Quick example queries

### Results Display
- Grid layout (2 columns on desktop)
- Trial cards with key information
- Phase and status badges with colors
- Hover effects and animations
- Pagination controls

### Trial Details
- Modal overlay with full information
- Comprehensive trial data
- Sponsors and facilities
- Conditions and interventions
- External links to ClinicalTrials.gov

### UI/UX Polish
- Smooth fade-in animations
- Hover state transitions
- Responsive design (mobile, tablet, desktop)
- Loading spinners with messages
- Empty states with suggestions
- Gradient backgrounds
- Custom scrollbars

## API Integration

The frontend connects to the backend API at `/api`:

- `POST /api/search` - Search trials
- `GET /api/trials/{nct_id}` - Get trial details
- `GET /api/filters` - Get aggregated filters
- `GET /api/trials/{nct_id}/similar` - Find similar trials

Vite proxy configuration automatically routes `/api` requests to `http://localhost:5000`.

## Customization

### Colors
Edit `tailwind.config.js` to customize the primary color palette:

```javascript
colors: {
  primary: {
    500: '#0ea5e9',  // Main color
    600: '#0284c7',
    700: '#0369a1',
  }
}
```

### Animations
Custom animations are defined in `tailwind.config.js`:
- `fade-in` - Smooth entrance
- `slide-up` - Slide from bottom
- `pulse-soft` - Gentle pulsing

## Performance

- Code splitting with Vite
- Lazy loading for modals
- Optimized re-renders with React
- Minimal bundle size
- Fast dev server with HMR

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

MIT
