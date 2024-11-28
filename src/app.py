from flask import Flask, render_template, jsonify, request, send_file, session
from .google_ads_client import GoogleAdsClient
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize without credentials
google_ads_client = GoogleAdsClient()

# Serve static files from the static directory
app.static_folder = 'static'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/initialize', methods=['POST'])
def initialize_client():
    try:
        credentials = request.json
        success = google_ads_client.initialize_client(credentials)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-status', methods=['GET'])
def check_status():
    return jsonify({'initialized': google_ads_client.is_initialized()})

@app.route('/api/campaigns/performance', methods=['POST'])
def campaign_performance():
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    try:
        data = request.json
        customer_id = data.get('customer_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Get campaign performance data
        performance_data = google_ads_client.get_campaign_performance(
            customer_id, start_date, end_date
        )
        
        # Get lead data for the period
        lead_data = google_ads_client.get_lead_insights(
            customer_id, start_date, end_date
        )
        
        if not performance_data or not lead_data:
            return jsonify({'error': 'No data available'}), 404
            
        # Calculate metrics
        total_leads = len(lead_data['leads'])
        total_cost = sum(lead['cost'] for lead in lead_data['leads']) if lead_data['leads'] else 0
        conversion_rate = (total_leads / performance_data['impressions'] * 100) if performance_data.get('impressions', 0) > 0 else 0
        avg_cost_per_lead = total_cost / total_leads if total_leads > 0 else 0
        
        # Prepare trend data
        dates = pd.date_range(start=start_date, end=end_date)
        leads_by_date = {date.strftime('%Y-%m-%d'): 0 for date in dates}
        for lead in lead_data['leads']:
            date = datetime.strptime(lead['creation_time'][:10], '%Y-%m-%d').strftime('%Y-%m-%d')
            leads_by_date[date] += 1
        
        # Prepare cost distribution data
        cost_by_category = {}
        for lead in lead_data['leads']:
            category = lead['category']
            cost_by_category[category] = cost_by_category.get(category, 0) + lead['cost']
        
        return jsonify({
            'performance': performance_data,
            'leads': lead_data,
            'metrics': {
                'total_leads': total_leads,
                'total_cost': total_cost,
                'conversion_rate': conversion_rate,
                'avg_cost_per_lead': avg_cost_per_lead
            },
            'trend_data': {
                'dates': list(leads_by_date.keys()),
                'leads': list(leads_by_date.values())
            },
            'cost_distribution': {
                'categories': list(cost_by_category.keys()),
                'values': list(cost_by_category.values())
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/insights', methods=['POST'])
def lead_insights():
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    try:
        data = request.json
        customer_id = data.get('customer_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        insights = google_ads_client.get_lead_insights(
            customer_id, start_date, end_date
        )
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns/geographic', methods=['POST'])
def geographic_performance():
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    try:
        data = request.json
        customer_id = data.get('customer_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        geo_data = google_ads_client.get_geographic_performance(
            customer_id, start_date, end_date
        )
        return jsonify(geo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns/competitor-insights', methods=['POST'])
def competitor_insights():
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    try:
        data = request.json
        customer_id = data.get('customer_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        competitor_data = google_ads_client.get_competitor_insights(
            customer_id, start_date, end_date
        )
        return jsonify(competitor_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<lead_id>', methods=['GET'])
def get_lead_details(lead_id):
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    customer_id = request.args.get('customer_id')
    
    try:
        lead_details = google_ads_client.get_lead_details(customer_id, lead_id)
        return jsonify(lead_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def export_csv():
    if not google_ads_client.is_initialized():
        return jsonify({'error': 'Client not initialized'}), 400
        
    customer_id = request.args.get('customer_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # Get lead data
        lead_data = google_ads_client.get_lead_insights(
            customer_id, start_date, end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(lead_data['leads'])
        
        # Create temporary file
        temp_file = 'temp_export.csv'
        df.to_csv(temp_file, index=False)
        
        # Send file and remove it after
        return_data = send_file(
            temp_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_export_{start_date}_to_{end_date}.csv'
        )
        
        @return_data.call_on_close
        def cleanup():
            os.remove(temp_file)
            
        return return_data
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/pdf')
def export_pdf():
    # Note: This is a placeholder for PDF export functionality
    # You would need to implement PDF generation using a library like reportlab or WeasyPrint
    return jsonify({'error': 'PDF export not yet implemented'}), 501

if __name__ == '__main__':
    app.run(debug=True)
