# Forest Tracker

Forest Tracker is a comprehensive web application designed to monitor forest health, analyze environmental data, and support conservation efforts. The application integrates satellite imagery analysis, economic correlations, research summarization, and policy recommendations to provide actionable insights for forest management and protection.

## Overview

The Forest Tracker application helps track forest conditions in regions like Makueni, Kenya, by processing satellite data to calculate vegetation health indicators. It offers tools for data analysis, correlation studies with economic factors, automated summarization of conservation research, and policy evaluation to guide decision-making for sustainable forest management.

## Features

- **Data Analysis**: Processes satellite bands to compute Normalized Difference Vegetation Index (NDVI) as a measure of forest health and biomass. Provides monthly and yearly trends to track changes over time.
- **Correlations**: Analyzes relationships between forest health (NDVI) and economic indicators like GDP, using statistical methods including Pearson correlation and linear regression to quantify environmental-economic impacts.
- **Summaries**: Uses AI-powered tools to extract and summarize key points from web articles on forest conservation, focusing on policy recommendations, environmental impacts, and region-specific insights.
- **Policy Recommendations**: Evaluates forest policies and provides recommendations based on data analysis and research insights.
- **Whistleblower Reports**: Allows anonymous submission of forest encroachment reports for community monitoring.
- **Dashboard**: Interactive dashboard displaying forest health metrics, encroachment levels, and policy evaluation results.
- **Authentication**: Secure login system with role-based access (user/admin) for protected resources.
- **Research Resources**: Platform for managing and accessing conservation research materials.

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js v14 or higher
- npm or yarn

### Backend Setup (Flask)

1. Create a virtual environment:
   ```bash
   python -m venv makueni
   ```

2. Activate the virtual environment:
   - On Windows: `makueni\Scripts\activate`
   - On macOS/Linux: `source makueni/bin/activate`

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (optional):
   Create a `.env` file in the root directory with:
   ```
   JWT_SECRET=your_secret_key_here
   ```

### Frontend Setup (Express.js)

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Configure environment (optional):
   Create a `.env` file in the root directory with:
   ```
   PORT=3000
   FLASK_BACKEND_URL=http://localhost:5000
   ```

## Running the Application

### Start the Backend

1. Activate the virtual environment:
   ```bash
   makueni\Scripts\activate
   ```

2. Run the Flask server:
   ```bash
   python app.py
   ```

   The backend will start on `http://localhost:5000`.

### Start the Frontend

1. Run the Express server:
   ```bash
   npm run dev
   ```

   The frontend will start on `http://localhost:3000`.

### Access the Application

- Open your browser and navigate to `http://localhost:3000`
- Use the login page to access authenticated features
- The dashboard provides an overview of forest health data
- Submit reports anonymously or access research resources

## Project Structure

```
.
├── app.py                          # Main Flask application
├── server.js                       # Express.js frontend server
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies
├── .env                            # Environment variables
├── analyis.py                      # NDVI calculation and trends
├── correlation_analysis.py         # Statistical correlations (NDVI vs GDP)
├── summary.py                      # AI-powered article summarization
├── research.py                     # Research resources management
├── agent_docs.py                   # Policy evaluation agent
├── dashboard.py                    # Dashboard data endpoints
├── register.py                     # User authentication
├── passwords.py                    # Password utilities
├── whistle.py                      # Whistleblower report handling
├── extraction.ipynb                # Jupyter notebook for data extraction
├── whistleblower_reports.json      # Stored reports data
├── makueni_bands.csv               # Satellite band data for Makueni
├── Makueni-FOLAREP.pdf             # Research document
├── MakueniBill.pdf                 # Policy document
├── views/                          # EJS templates
│   ├── landing.ejs                 # Home page
│   ├── login.ejs                   # Login page
│   ├── dashboard.ejs               # Analytics dashboard
│   ├── report.ejs                  # Report submission form
│   ├── resources.ejs               # Research resources page
│   └── partials/                   # Reusable template components
│       ├── header.ejs              # Navigation header
│       └── footer.ejs              # Footer
├── public/                         # Static assets
│   ├── css/
│   │   └── styles.css              # Main stylesheet
│   └── js/
│       └── forest-background.js    # Animated forest background
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login

### Research
- `GET /api/research/resources` - Get research resources (authenticated)
- `POST /api/research/resources` - Add research resource (admin only)
- `POST /api/research/summarize_article` - Summarize web article (authenticated)

### Dashboard
- `GET /api/dashboard/data` - Get dashboard metrics
- `GET /api/dashboard/policy-results` - Get policy evaluation results
- `POST /api/dashboard/ndvi/predict` - Predict GDP from NDVI value

### Reports
- `POST /api/whistle/submit` - Submit anonymous report
- `GET /api/whistle/reports` - Get all reports (authenticated)

### Data Analysis
- `GET /api/ndvi/trend` - Get NDVI trend data
- `GET /api/evaluate` - Run policy evaluation

## Usage

1. **Data Analysis**: The application automatically processes satellite data to compute NDVI values, providing insights into forest health trends.

2. **Correlation Studies**: Analyze how forest conditions correlate with economic indicators to understand the broader impacts of conservation efforts.

3. **Research Summarization**: Input URLs of conservation articles to get AI-generated summaries focusing on key recommendations and insights.

4. **Policy Evaluation**: Access policy recommendations based on data analysis and current forest conditions.

5. **Community Reporting**: Submit anonymous reports of forest encroachment to contribute to monitoring efforts.

## Contributing

To contribute to Forest Tracker:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

ISC License

## Notes

- The application uses in-memory storage for sessions and resources. For production, consider using databases like PostgreSQL or MongoDB.
- API endpoints may require authentication; ensure proper JWT token handling.
- The forest background animation enhances the user interface with an immersive theme.
- Data analysis relies on satellite imagery; ensure data sources are updated regularly for accurate results.
