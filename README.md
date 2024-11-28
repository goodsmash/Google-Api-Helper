# Google Ads Marketing Analytics Platform

A comprehensive web application for analyzing and visualizing Google Ads Local Services campaign data, providing marketing teams with detailed insights into lead performance and campaign effectiveness.

## Features

- **Dashboard Analytics**
  - Real-time performance metrics
  - Lead trend analysis
  - Cost distribution visualization
  - Campaign performance tracking

- **Lead Management**
  - Detailed lead information
  - Conversion tracking
  - Lead status monitoring
  - Cost analysis

- **Campaign Analysis**
  - Performance metrics
  - Geographic distribution
  - Competitive insights
  - Market position analysis

- **Data Export**
  - CSV export functionality
  - PDF report generation (coming soon)

## Technical Requirements

- Python 3.8+
- Google Ads API access
- Valid API credentials

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd google-ads-analytics
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Google Ads API credentials:
   - Create a `google-ads.yaml` file in the config directory
   - Add your API credentials:
```yaml
developer_token: "YOUR_DEVELOPER_TOKEN"
client_id: "YOUR_CLIENT_ID"
client_secret: "YOUR_CLIENT_SECRET"
refresh_token: "YOUR_REFRESH_TOKEN"
```

5. Start the application:
```bash
python src/app.py
```

## Usage

1. Access the application at `http://localhost:5000`
2. Enter your Google Ads Customer ID
3. Use the dashboard to:
   - View performance metrics
   - Analyze lead data
   - Track campaign performance
   - Generate reports

## API Endpoints

### Campaign Performance
- `POST /api/campaigns/performance`
  - Parameters: customer_id, start_date, end_date

### Lead Insights
- `POST /api/leads/insights`
  - Parameters: customer_id, start_date, end_date

### Geographic Analysis
- `POST /api/campaigns/geographic`
  - Parameters: customer_id, start_date, end_date

### Competitive Insights
- `POST /api/campaigns/competitor-insights`
  - Parameters: customer_id, start_date, end_date

### Data Export
- `GET /api/export/csv`
- `GET /api/export/pdf`

## Security Considerations

- Store API credentials securely
- Use environment variables for sensitive data
- Implement rate limiting
- Monitor API usage
- Regular security audits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
