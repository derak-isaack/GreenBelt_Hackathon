const express = require('express');
const path = require('path');
const axios = require('axios');
const cookieParser = require('cookie-parser');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const FLASK_BACKEND_URL = process.env.FLASK_BACKEND_URL || 'http://localhost:5000';

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// Set view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Store for session (in production, use Redis or proper session store)
let sessions = {};

// Helper function to make requests to Flask backend
async function makeBackendRequest(method, endpoint, data = null, token = null) {
  try {
    const config = {
      method,
      url: `${FLASK_BACKEND_URL}${endpoint}`,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    if (data) {
      config.data = data;
    }

    const response = await axios(config);
    return { success: true, data: response.data, status: response.status };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message,
      status: error.response?.status || 500,
    };
  }
}

// ===================
// API Routes (Proxy to Flask)
// ===================

// Auth routes
app.post('/api/auth/login', async (req, res) => {
  const result = await makeBackendRequest('POST', '/auth/login', req.body);
  if (result.success) {
    // Store token in session (simplified - use proper session management in production)
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessions[sessionId] = { token: result.data.token, user: req.body.username };
    res.cookie('sessionId', sessionId, { httpOnly: true, maxAge: 8 * 60 * 60 * 1000 }); // 8 hours
    res.json({ ...result.data, username: req.body.username });
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// Middleware to check authentication for API routes
function checkAuth(req, res, next) {
  // Check Authorization header (from localStorage token)
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    req.token = authHeader.split(' ')[1];
    return next();
  }
  
  // Check session cookie (from server-side login)
  const sessionId = req.cookies.sessionId;
  if (sessionId && sessions[sessionId]) {
    req.token = sessions[sessionId].token;
    return next();
  }
  
  return res.status(401).json({ error: 'Authentication required' });
}

// Middleware to check authentication for page routes (redirects to login)
// Note: Client-side checks in the pages will also redirect if no localStorage token exists as a backup
function requireAuth(req, res, next) {
  // Check session cookie (from server-side login)
  const sessionId = req.cookies.sessionId;
  if (sessionId && sessions[sessionId]) {
    req.user = sessions[sessionId].user;
    return next();
  }
  
  // If no session, redirect to login with redirect parameter
  const redirectUrl = req.originalUrl;
  res.redirect(`/login?redirect=${encodeURIComponent(redirectUrl)}`);
}

// Research routes
app.get('/api/research/resources', checkAuth, async (req, res) => {
  const result = await makeBackendRequest('GET', '/research/resources', null, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

app.post('/api/research/resources', checkAuth, async (req, res) => {
  const result = await makeBackendRequest('POST', '/research/resources', req.body, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

app.post('/api/research/summarize_article', checkAuth, async (req, res) => {
  const result = await makeBackendRequest('POST', '/research/summarize_article', req.body, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// Whistleblower routes
app.post('/api/whistle/submit', async (req, res) => {
  // No auth required for anonymous reports
  const reportData = {
    report: `${req.body.location || ''}\n\n${req.body.incidentDetails || ''}`,
    attachments: req.body.attachments || [],
  };
  const result = await makeBackendRequest('POST', '/whistle/submit', reportData);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// Dashboard routes
app.get('/api/dashboard/policy-results', async (req, res) => {
  const result = await makeBackendRequest('GET', '/dashboard/policy-results');
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

app.get('/api/dashboard/data', async (req, res) => {
  // Get policy results and transform to dashboard data format
  const policyResult = await makeBackendRequest('GET', '/dashboard/policy-results');
  
  // Get reports for dashboard
  const reportsResult = await makeBackendRequest('GET', '/whistle/reports').catch(() => ({ success: false, data: [] }));
  
  // Transform policy results to dashboard format
  let dashboardData = [];
  if (policyResult.success && policyResult.data.results) {
    // Transform the policy evaluation results into dashboard format
    // This is a placeholder - adjust based on actual policy_evaluation output structure
    dashboardData = [{
      forestHealth: 75,
      encroachmentLevel: 25,
      locationData: ['Forest Area 1', 'Forest Area 2'],
    }];
  }
  
  res.json(dashboardData);
});

app.get('/api/whistle/reports', async (req, res) => {
  // Read from the JSON file that Flask writes to
  const fs = require('fs');
  const reportsFile = path.join(__dirname, 'whistleblower_reports.json');
  
  try {
    if (fs.existsSync(reportsFile)) {
      const reports = JSON.parse(fs.readFileSync(reportsFile, 'utf8'));
      // Transform to match frontend format
      const transformedReports = reports.map((report, index) => {
        const reportText = report.report || '';
        const lines = reportText.split('\n');
        return {
          id: report.id || `report-${index}`,
          location: lines[0] || 'Unknown',
          incidentDetails: lines.slice(1).join('\n') || reportText,
          timestamp: report.timestamp 
            ? (new Date(report.timestamp).getTime() * 1000000) 
            : (Date.now() * 1000000), // Convert to nanoseconds format
        };
      });
      res.json(transformedReports);
    } else {
      res.json([]);
    }
  } catch (error) {
    console.error('Error reading reports:', error);
    res.json([]);
  }
});

// Evaluate route
app.get('/api/evaluate', async (req, res) => {
  const result = await makeBackendRequest('GET', '/evaluate');
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// ===================
// Frontend Routes
// ===================

app.get('/', (req, res) => {
  res.render('landing', { title: 'Forest Tracker - Home', currentPath: '/' });
});

app.get('/resources', requireAuth, (req, res) => {
  res.render('resources', { title: 'Forest Tracker - Resources', currentPath: '/resources' });
});

app.get('/report', (req, res) => {
  res.render('report', { title: 'Forest Tracker - Report Encroachment', currentPath: '/report' });
});

app.get('/dashboard', requireAuth, (req, res) => {
  res.render('dashboard', { title: 'Forest Tracker - Dashboard', currentPath: '/dashboard' });
});

app.get('/login', (req, res) => {
  res.render('login', { title: 'Forest Tracker - Login', currentPath: '/login' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Forest Tracker Express server running on http://localhost:${PORT}`);
  console.log(`Backend API: ${FLASK_BACKEND_URL}`);
});

