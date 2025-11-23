# Forest Tracker

Forest Tracker is a specialized web application for monitoring forest degradation in Makueni County, Kenya, using Sentinel-1 satellite radar data. The system employs the Radar Forest Degradation Index (RFDI) to detect forest disturbances, with a threshold of 0.61 used to categorize areas as alerts indicating potential logging, encroachment, or other degradation activities.

## Overview

Makueni County, located in a semi-arid region of Kenya, contains eight key forests that face significant threats from human encroachment, illegal logging, and agricultural expansion. These areas are often neglected in national conservation efforts due to their arid conditions and remote locations. Forest Tracker addresses this gap by providing real-time monitoring of forest health across these eight forests, enabling community organizations and policymakers to take timely action against degradation.

The application processes Sentinel-1 satellite data to compute RFDI values, tracks monthly trends, correlates forest health with economic indicators, and generates AI-powered policy recommendations tailored to the specific challenges faced by Makueni's forest ecosystems.

## Features

- **RFDI Analysis**: Processes Sentinel-1 satellite radar data (VV and VH polarizations) to compute the Radar Forest Degradation Index (RFDI). Uses a threshold of 0.61 to identify forest degradation alerts, providing monthly and yearly trends to track disturbances over time.
- **Forest Health Monitoring**: Tracks the health of eight individual forests in Makueni County (Chyulu, Katende, Kibwezi, Kilungu, Kivale, Makuli, Mavindu, Mulooni) relative to county-wide degradation levels, enabling targeted conservation efforts.
- **Correlations**: Analyzes relationships between forest degradation (RFDI alerts) and economic indicators like GDP, using statistical methods including Pearson correlation and linear regression to quantify environmental-economic impacts in semi-arid regions.
- **Policy Evaluation**: Generates AI-powered policy recommendations specifically tailored to Makueni's forests, addressing threats like illegal logging, agricultural encroachment, and ecosystem degradation in arid environments.
- **Whistleblower Reports**: Allows anonymous submission of forest encroachment reports for community-based monitoring of logging and land-use changes.
- **Dashboard**: Interactive dashboard displaying RFDI trends, forest health scores, degradation alerts, and policy evaluation results for each of the eight Makueni forests.
- **Authentication**: Secure login system with role-based access (researcher/admin) for protected resources and data analysis tools.
- **Research Resources**: Platform for managing and accessing conservation research materials focused on semi-arid forest ecosystems.

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

4. Set up environment variables:
    Create a `.env` file in the root directory with:
    ```
    JWT_SECRET=your_secret_key_here
    GEMINI_API_KEY=your_google_gemini_api_key_here
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
├── analysis.py                     # RFDI calculation and trends from Sentinel-1 data
├── correlation_analysis.py         # Statistical correlations (RFDI alerts vs GDP)
├── summary.py                      # AI-powered article summarization
├── research.py                     # Research resources management
├── agent_docs.py                   # Policy evaluation agent
├── dashboard.py                    # Dashboard data endpoints
├── register.py                     # User authentication
├── passwords.py                    # Password utilities
├── whistle.py                      # Whistleblower report handling
├── extraction.ipynb                # Jupyter notebook for data extraction
├── whistleblower_reports.json      # Stored reports data
├── SentinelMakueni.csv             # Sentinel-1 satellite data for Makueni forests
├── Makueni_interpolated.csv        # Processed Sentinel-1 data with RFDI calculations
├── tree_cover_loss_by_driver.csv   # Forest loss drivers data
├── Makueni-FOLAREP.pdf             # Research document on Makueni forests
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
- `GET /api/ndvi/trend` - Get RFDI trend data for Sentinel-1 analysis
- `GET /api/dashboard/forest-health` - Get forest health scores based on RFDI alerts
- `GET /api/dashboard/filtered-data` - Get filtered Sentinel-1 data with RFDI alerts
- `GET /api/evaluate` - Run AI-powered policy evaluation for Makueni forests

## Usage

1. **RFDI Monitoring**: The application processes Sentinel-1 satellite data to compute RFDI values and identify degradation alerts above the 0.61 threshold, tracking monthly trends across Makueni's eight forests.

2. **Forest Health Assessment**: Compare individual forest health scores against county-wide degradation levels to prioritize conservation efforts in the most threatened areas.

3. **Correlation Analysis**: Examine relationships between forest degradation alerts and economic indicators to quantify the socio-economic impacts of conservation in semi-arid regions.

4. **Policy Evaluation**: Generate AI-powered policy recommendations specifically addressing Makueni's challenges with illegal logging, agricultural encroachment, and ecosystem degradation in arid forest environments.

5. **Community Monitoring**: Submit anonymous reports of forest encroachment and logging activities to support ground-level monitoring efforts in remote semi-arid areas.

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

- The application focuses on Makueni County's eight forests: Chyulu, Katende, Kibwezi, Kilungu, Kivale, Makuli, Mavindu, and Mulooni, which face significant threats from logging and agricultural expansion in semi-arid conditions.
- RFDI threshold of 0.61 is calibrated for Sentinel-1 data to detect forest degradation in arid environments; this may need adjustment based on local conditions.
- The application uses in-memory storage for sessions and resources. For production, consider using databases like PostgreSQL or MongoDB.
- API endpoints may require authentication; ensure proper JWT token handling and GEMINI_API_KEY configuration.
- The forest background animation enhances the user interface with an immersive theme representing Makueni's ecosystems.
- Sentinel-1 data processing relies on regular satellite imagery updates; ensure data sources are refreshed to maintain accuracy for real-time forest monitoring.
