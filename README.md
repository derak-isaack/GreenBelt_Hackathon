# Forest Tracker - Express.js Frontend

This is the Express.js frontend for the Forest Tracker application. It connects to the Flask backend API and provides a beautiful forest-themed interface for monitoring, reporting, and analyzing forest health data.

## Features

- 🌲 **Forest Theme Background** - Animated canvas background with mist/fog effects
- 📊 **Dashboard** - Real-time monitoring of forest health and encroachment levels
- 📝 **Report System** - Anonymous reporting of forest encroachments
- 📚 **Resources** - Educational materials and conservation guides
- 🔐 **Authentication** - JWT-based authentication for protected resources

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Flask backend running (default: http://localhost:5000)

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (optional, defaults are provided):
```bash
PORT=3000
FLASK_BACKEND_URL=http://localhost:5000
```

## Running the Server

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The server will start on `http://localhost:3000` by default.

## API Endpoints

The Express server proxies requests to the Flask backend:

- `POST /api/auth/login` - User authentication
- `GET /api/research/resources` - Get research resources (requires auth)
- `POST /api/research/resources` - Add research resource (requires admin auth)
- `POST /api/research/summarize_article` - Summarize article (requires auth)
- `POST /api/whistle/submit` - Submit anonymous report
- `GET /api/whistle/reports` - Get all reports
- `GET /api/dashboard/policy-results` - Get policy evaluation results
- `GET /api/dashboard/data` - Get dashboard data
- `GET /api/evaluate` - Evaluate policy

## Frontend Routes

- `/` - Landing page
- `/resources` - Educational resources
- `/report` - Report encroachment form
- `/dashboard` - Analytics dashboard

## Project Structure

```
.
├── server.js              # Main Express server
├── package.json           # Dependencies
├── views/                 # EJS templates
│   ├── landing.ejs       # Landing page
│   ├── dashboard.ejs     # Dashboard page
│   ├── report.ejs        # Report page
│   ├── resources.ejs     # Resources page
│   └── partials/         # Reusable components
│       ├── header.ejs    # Navigation header
│       └── footer.ejs    # Footer
├── public/                # Static assets
│   ├── css/
│   │   └── styles.css    # Main stylesheet
│   └── js/
│       └── forest-background.js  # Forest animation
└── README.md
```

## Notes

- The backend API endpoints have not been tested yet. You may need to adjust the API routes in `server.js` based on your actual Flask backend implementation.
- The forest background animation uses HTML5 Canvas for a beautiful animated effect.
- Session management is simplified (in-memory). For production, use Redis or a proper session store.

## Troubleshooting

1. **Backend Connection Issues**: Make sure your Flask backend is running on the configured port (default: 5000)
2. **CORS Issues**: If you encounter CORS errors, you may need to configure CORS in your Flask backend
3. **Port Already in Use**: Change the PORT in `.env` or use a different port

## License

ISC

