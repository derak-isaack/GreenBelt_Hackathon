const express = require('express');
const path = require('path');
const axios = require('axios');
const cookieParser = require('cookie-parser');
const http = require('http');
const { URL } = require('url');
const multer = require('multer');
const FormData = require('form-data');
const querystring = require('querystring');
const fs = require('fs');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const JWT_SECRET = process.env.JWT_SECRET || 'CHANGE_THIS_SECRET';

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

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

// Store for session (in production, use Redis or proper session store)

// Helper functions for session persistence
function loadSessions() {
  try {
    if (fs.existsSync('sessions.json')) {
      const data = fs.readFileSync('sessions.json', 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading sessions:', error);
  }
  return {};
}

function saveSessions() {
  try {
    fs.writeFileSync('sessions.json', JSON.stringify(sessions, null, 2));
  } catch (error) {
    console.error('Error saving sessions:', error);
  }
}

let sessions = loadSessions();

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

// Proxy function to forward requests to Flask backend preserving multipart data
function proxyToBackend(req, res, endpoint) {
  const url = new URL(FLASK_BACKEND_URL);
  const options = {
    hostname: url.hostname,
    port: url.port,
    path: endpoint,
    method: req.method,
    headers: {
      ...req.headers,
      authorization: req.headers.authorization || (req.token ? `Bearer ${req.token}` : undefined),
    },
  };
  delete options.headers.host;

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err);
    res.status(500).json({ error: 'Proxy error' });
  });

  req.pipe(proxyReq);
}

// ===================
// API Routes (Proxy to Flask)
// ===================

// Auth routes
app.post('/api/auth/login', async (req, res) => {
  const result = await makeBackendRequest('POST', '/auth/login', req.body);
  if (result.success) {

    const token = result.data.token;
    let role = 'user';  // fallback

    try {
      const payload = token.split('.')[1];
      const decoded = JSON.parse(Buffer.from(payload, 'base64').toString());
      role = decoded.role || 'user';
    } catch (e) {
      console.error("Error decoding token:", e);
    }

    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessions[sessionId] = { token, user: req.body.username, role };
    saveSessions();

    res.cookie('sessionId', sessionId, {
      httpOnly: true,
      maxAge: 8 * 60 * 60 * 1000,
    });

    res.json({ ...result.data, username: req.body.username, role });
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// Middleware to check authentication for API routes
function checkAuth(req, res, next) {
  console.log(`checkAuth: ${req.method} ${req.path}, headers auth: ${!!req.headers.authorization}, cookie sessionId: ${!!req.cookies.sessionId}`);
  let token = null;

  // Check Authorization header
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const value = authHeader.split(' ')[1];
    console.log('checkAuth: auth header value:', value);
    if (sessions[value]) {
      // sessionId provided, retrieve JWT from sessions
      token = sessions[value].token;
      console.log('checkAuth: retrieved JWT from sessions for sessionId');
    } else {
      // assume it's the JWT directly
      token = value;
      console.log('checkAuth: using value as JWT');
    }
  }

  // If no token from header, check session cookie
  if (!token) {
    const sessionId = req.cookies.sessionId;
    console.log('checkAuth: sessionId from cookie:', sessionId, 'exists in sessions:', !!sessions[sessionId]);
    if (sessionId && sessions[sessionId]) {
      token = sessions[sessionId].token;
      console.log('checkAuth: retrieved JWT from sessions for cookie sessionId');
    }
  }

  if (token) {
    try {
      jwt.verify(token, JWT_SECRET);
      req.token = token;
      console.log('checkAuth: req.token set to JWT');
      return next();
    } catch (err) {
      console.log('checkAuth: JWT verification failed:', err.message);
      return res.status(401).json({ error: 'Invalid or expired token' });
    }
  }

  console.log('checkAuth: no auth found, returning 401');
  return res.status(401).json({ error: 'Authentication required' });
}

// Middleware to check authentication for page routes (redirects to login)
// Note: Client-side checks in the pages will also redirect if no localStorage token exists as a backup
function requireAuth(req, res, next) {
  console.log(`requireAuth: ${req.method} ${req.path}, sessionId cookie: ${!!req.cookies.sessionId}`);
  // Check session cookie (from server-side login)
  const sessionId = req.cookies.sessionId;
  if (sessionId && sessions[sessionId]) {
    req.user = sessions[sessionId].user;
    req.role = sessions[sessionId].role;
    console.log('requireAuth: session valid, proceeding');
    return next();
  }

  console.log('requireAuth: no valid session, redirecting to login');
  // If no session, redirect to login with redirect parameter
  const redirectUrl = req.originalUrl;
  res.redirect(`/login?redirect=${encodeURIComponent(redirectUrl)}`);
}

// Middleware to check admin role
function requireAdmin(req, res, next) {
  console.log(`requireAdmin: ${req.method} ${req.path}, role: ${req.role}`);
  if (req.role === 'admin') {
    console.log('requireAdmin: admin access granted');
    return next();
  }

  console.log('requireAdmin: access denied, redirecting to dashboard');
  res.redirect('/dashboard');
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
    forest: req.body.forest || '',
  };
  const result = await makeBackendRequest('POST', '/whistle/submit', reportData);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

// Dashboard routes
app.get('/api/dashboard/policy-results', checkAuth, async (req, res) => {
  console.log('Dashboard policy-results request headers:', req.headers.authorization ? 'Auth header present' : 'No auth header');
  const result = await makeBackendRequest('GET', '/dashboard/policy-results?' + querystring.stringify(req.query), null, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    console.log('Backend error for policy-results:', result.status, result.error);
    res.status(result.status).json({ error: result.error });
  }
});

app.post('/api/dashboard/ndvi/predict', checkAuth, async (req, res) => {
  console.log('/api/dashboard/ndvi/predict: request received');
  const result = await makeBackendRequest('POST', '/dashboard/ndvi/predict', req.body, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    console.log('Backend error for ndvi/predict:', result.status, result.error);
    res.status(result.status).json({ error: result.error });
  }
});

app.get('/api/dashboard/policy-pdf', checkAuth, async (req, res) => {
  console.log('/api/dashboard/policy-pdf: request received');
  const result = await makeBackendRequest('GET', '/dashboard/policy-pdf', null, req.token);
  if (result.success) {
    // For PDF downloads, we need to set appropriate headers
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="policy_recommendations.pdf"');
    res.send(result.data);
  } else {
    console.log('Backend error for policy-pdf:', result.status, result.error);
    res.status(result.status).json({ error: result.error });
  }
});

app.get('/api/dashboard/data', checkAuth, async (req, res) => {
  console.log('/api/dashboard/data: request received, query params:', req.query);

  // Initialize empty dashboard data
  let dashboardData = [];

  console.log('/api/dashboard/data: returning dashboardData length:', dashboardData.length);
  res.json(dashboardData);
});

app.get('/api/s1/trend', async (req, res) => {
  const result = await makeBackendRequest('GET', '/ndvi/api/s1/trend' + '?' + querystring.stringify(req.query));
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

app.get('/filtered-data', async (req, res) => {
  const result = await makeBackendRequest('GET', `/dashboard/filtered-data?${querystring.stringify(req.query)}`);
  if (result.success) {
    res.json(result.data);
  } else {
    res.status(result.status).json({ error: result.error });
  }
});

app.get('/api/whistle/reports', checkAuth, async (req, res) => {
  console.log('/api/whistle/reports: request received');
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
      console.log('/api/whistle/reports: returning reports count:', transformedReports.length);
      res.json(transformedReports);
    } else {
      console.log('/api/whistle/reports: no reports file found');
      res.json([]);
    }
  } catch (error) {
    console.error('Error reading reports:', error);
    res.json([]);
  }
});

// Admin routes - handle file uploads with multer
app.post('/api/admin/upload', checkAuth, upload.single('file'), async (req, res) => {
  console.log('/api/admin/upload: processing upload');
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }

  const form = new FormData();
  form.append('file', req.file.buffer, {
    filename: req.file.originalname,
    contentType: req.file.mimetype,
  });

  try {
    const response = await axios({
      method: 'POST',
      url: `${FLASK_BACKEND_URL}/admin/upload`,
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${req.token}`,
      },
      data: form,
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: error.response?.data?.error || error.message });
  }
});

app.get('/api/admin/uploads', checkAuth, (req, res) => {
  console.log('/api/admin/uploads: proxying request');
  proxyToBackend(req, res, '/admin/uploads');
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

app.post('/login', async (req, res) => {
  console.log('Login POST: attempting login for user:', req.body.username);
  const result = await makeBackendRequest('POST', '/auth/login', req.body);
  if (result.success) {
    console.log('Login POST: backend login success');
    // Decode token to get role
    const token = result.data.token;
    let role = 'user'; // default
    try {
      const payload = token.split('.')[1];
      const decoded = JSON.parse(Buffer.from(payload, 'base64').toString());
      role = decoded.role || 'user';
      console.log('Login POST: decoded role:', role);
    } catch (e) {
      console.error('Login POST: Error decoding token:', e);
    }

    // Store token and role in session
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessions[sessionId] = { token: result.data.token, user: req.body.username, role: role };
    saveSessions();
    res.cookie('sessionId', sessionId, { httpOnly: true, maxAge: 8 * 60 * 60 * 1000 }); // 8 hours
    console.log('Login POST: session created, cookie set, redirecting based on role');

    // Redirect based on role
    if (role === 'researcher') {
      res.redirect('/resources');
    } else {
      res.redirect('/dashboard');
    }
  } else {
    console.log('Login POST: backend login failed:', result.error);
    // Redirect back to login with error
    res.redirect(`/login?error=${encodeURIComponent(result.error)}`);
  }
});

app.get('/', (req, res) => {
  res.render('landing', { title: 'Forest Tracker - Home', currentPath: '/' });
});

app.get('/resources', requireAuth, (req, res) => {
  res.render('resources', { title: 'Forest Tracker - Resources', currentPath: '/resources' });
});

app.get('/report', (req, res) => {
  res.render('report', { title: 'Forest Tracker - Report Encroachment', currentPath: '/report' });
});

app.get('/dashboard', (req, res) => {
  let role = 'user'; // default
  const sessionId = req.cookies.sessionId;
  if (sessionId && sessions[sessionId]) {
    role = sessions[sessionId].role;
  }
  res.render('dashboard', { title: 'Forest Tracker - Dashboard', currentPath: '/dashboard', role });
});

app.get('/admin', requireAuth, requireAdmin, (req, res) => {
  res.render('admin', { title: 'Forest Tracker - Admin Portal', currentPath: '/admin', role: req.role });
});

app.get('/login', (req, res) => {
  const error = req.query.error;
  res.render('login', { title: 'Forest Tracker - Login', currentPath: '/login', error: error });
});

app.get('/api/dashboard/forest-health', checkAuth, async (req, res) => {
  console.log('/api/dashboard/forest-health: request received, query params:', req.query);
  const result = await makeBackendRequest('GET', '/dashboard/forest-health?' + querystring.stringify(req.query), null, req.token);
  if (result.success) {
    res.json(result.data);
  } else {
    console.log('Backend error for forest-health:', result.status, result.error);
    res.status(result.status).json({ error: result.error });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Forest Tracker Express server running on http://localhost:${PORT}`);
  console.log(`Backend API: ${FLASK_BACKEND_URL}`);
});

