from google.ads.googleads.client import GoogleAdsClient as GoogleAdsClientLib
from google.ads.googleads.errors import GoogleAdsException
import os
from datetime import datetime, timedelta
import pandas as pd

class GoogleAdsClient:
    def __init__(self, credentials=None):
        """Initialize Google Ads client with credentials."""
        self.client = None
        self.credentials = credentials

    def initialize_client(self, credentials=None):
        """Initialize the client with provided credentials."""
        if credentials:
            self.credentials = credentials
        
        if not self.credentials:
            return False

        try:
            config = {
                'developer_token': self.credentials.get('developer_token'),
                'client_id': self.credentials.get('client_id'),
                'client_secret': self.credentials.get('client_secret'),
                'refresh_token': self.credentials.get('refresh_token'),
                'use_proto_plus': True
            }
            
            self.client = GoogleAdsClientLib.load_from_dict(config)
            return True
        except Exception as e:
            print(f"Error initializing client: {str(e)}")
            return False

    def is_initialized(self):
        """Check if client is initialized."""
        return self.client is not None

    def get_lead_statistics(self, customer_id, query_type='today', start_date=None, end_date=None, lead_type=None):
        """Get lead statistics based on query type and filters."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Build date range condition
            date_condition = self._build_date_condition(query_type, start_date, end_date)
            
            # Build lead type condition
            lead_type_condition = ""
            if lead_type:
                lead_type_condition = f" AND lead.type = '{lead_type}'"
            
            query = f"""
                SELECT
                    lead.id,
                    lead.lead_id,
                    lead.type,
                    lead.status,
                    lead.creation_date_time,
                    lead.category,
                    lead.service,
                    lead.business_name,
                    lead.contact_info.phone_number,
                    lead.contact_info.email,
                    lead.credit_info.credit_state,
                    lead.credit_info.update_time,
                    metrics.cost_micros,
                    metrics.conversions
                FROM lead
                WHERE {date_condition}{lead_type_condition}
                ORDER BY lead.creation_date_time DESC
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            leads = []
            for row in response:
                lead = row.lead
                leads.append({
                    'id': lead.id,
                    'lead_id': lead.lead_id,
                    'type': lead.type,
                    'status': lead.status,
                    'creation_time': lead.creation_date_time,
                    'category': lead.category,
                    'service': lead.service,
                    'business_name': lead.business_name,
                    'phone': lead.contact_info.phone_number,
                    'email': lead.contact_info.email,
                    'credit_state': lead.credit_info.credit_state,
                    'credit_update_time': lead.credit_info.update_time,
                    'cost': row.metrics.cost_micros / 1000000,
                    'conversions': row.metrics.conversions
                })
            
            # Calculate statistics
            stats = self._calculate_statistics(leads)
            
            return {
                'leads': leads,
                'statistics': stats
            }
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_lead_conversations(self, customer_id, lead_id):
        """Get conversation details for a specific lead."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = f"""
                SELECT
                    lead.id,
                    lead.conversation.type,
                    lead.conversation.message_content,
                    lead.conversation.timestamp
                FROM lead
                WHERE lead.id = '{lead_id}'
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            conversations = []
            for row in response:
                conv = row.lead.conversation
                conversations.append({
                    'type': conv.type,
                    'content': conv.message_content,
                    'timestamp': conv.timestamp
                })
                
            return conversations
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_employee_data(self, customer_id):
        """Get employee information."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    employee.id,
                    employee.name,
                    employee.role,
                    employee.status
                FROM employee
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            employees = []
            for row in response:
                emp = row.employee
                employees.append({
                    'id': emp.id,
                    'name': emp.name,
                    'role': emp.role,
                    'status': emp.status
                })
                
            return employees
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_campaign_id(self, customer_id):
        """Get Local Services campaign ID."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    campaign.id,
                    campaign.name
                FROM campaign
                WHERE campaign.advertising_channel_type = 'LOCAL_SERVICES'
                LIMIT 1
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                return row.campaign.id
                
            return None
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_campaign_data(self, customer_id):
        """Get Local Services campaign and budget information."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign_budget.id,
                    campaign_budget.period,
                    campaign_budget.amount_micros,
                    campaign_budget.type,
                    campaign.local_services_campaign_settings.category_bids
                FROM campaign
                WHERE campaign.advertising_channel_type = 'LOCAL_SERVICES'
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            campaigns = []
            for row in response:
                campaign = row.campaign
                budget = row.campaign_budget
                campaigns.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'status': campaign.status,
                    'budget_id': budget.id,
                    'budget_period': budget.period,
                    'budget_amount': budget.amount_micros / 1000000,
                    'budget_type': budget.type,
                    'category_bids': campaign.local_services_campaign_settings.category_bids
                })
            
            return campaigns
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_detailed_lead_data(self, customer_id, query_type='today', start_date=None, end_date=None):
        """Get comprehensive lead information including contact details and credit information."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            date_condition = self._build_date_condition(query_type, start_date, end_date)
            
            query = f"""
                SELECT
                    local_services_lead.lead_type,
                    local_services_lead.category_id,
                    local_services_lead.service_id,
                    local_services_lead.contact_details,
                    local_services_lead.lead_status,
                    local_services_lead.creation_date_time,
                    local_services_lead.locale,
                    local_services_lead.lead_charged,
                    local_services_lead.credit_details.credit_state,
                    local_services_lead.credit_details.credit_state_last_update_date_time
                FROM local_services_lead
                WHERE {date_condition}
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            leads = []
            for row in response:
                lead = row.local_services_lead
                leads.append({
                    'lead_type': lead.lead_type,
                    'category_id': lead.category_id,
                    'service_id': lead.service_id,
                    'contact_details': lead.contact_details,
                    'lead_status': lead.lead_status,
                    'creation_time': lead.creation_date_time,
                    'locale': lead.locale,
                    'lead_charged': lead.lead_charged,
                    'credit_state': lead.credit_details.credit_state,
                    'credit_update_time': lead.credit_details.credit_state_last_update_date_time
                })
            
            return leads
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_lead_conversations_detailed(self, customer_id, lead_id=None):
        """Get detailed conversation data including phone calls and messages."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            lead_condition = f"WHERE local_services_lead_conversation.lead = '{lead_id}'" if lead_id else ""
            
            query = f"""
                SELECT
                    local_services_lead_conversation.id,
                    local_services_lead_conversation.conversation_channel,
                    local_services_lead_conversation.participant_type,
                    local_services_lead_conversation.lead,
                    local_services_lead_conversation.event_date_time,
                    local_services_lead_conversation.phone_call_details.call_duration_millis,
                    local_services_lead_conversation.phone_call_details.call_recording_url,
                    local_services_lead_conversation.message_details.text,
                    local_services_lead_conversation.message_details.attachment_urls
                FROM local_services_lead_conversation
                {lead_condition}
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            conversations = []
            for row in response:
                conv = row.local_services_lead_conversation
                conversations.append({
                    'id': conv.id,
                    'channel': conv.conversation_channel,
                    'participant_type': conv.participant_type,
                    'lead_id': conv.lead,
                    'event_time': conv.event_date_time,
                    'call_duration': conv.phone_call_details.call_duration_millis if conv.conversation_channel == 'PHONE_CALL' else None,
                    'call_recording_url': conv.phone_call_details.call_recording_url if conv.conversation_channel == 'PHONE_CALL' else None,
                    'message_text': conv.message_details.text if conv.conversation_channel == 'MESSAGE' else None,
                    'attachment_urls': conv.message_details.attachment_urls if conv.conversation_channel == 'MESSAGE' else None
                })
            
            return conversations
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_verification_artifacts(self, customer_id, artifact_type=None):
        """Get verification artifacts for licenses, insurance, and background checks."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            type_condition = f"WHERE local_services_verification_artifact.artifact_type = '{artifact_type}'" if artifact_type else ""
            
            query = f"""
                SELECT
                    local_services_verification_artifact.id,
                    local_services_verification_artifact.creation_date_time,
                    local_services_verification_artifact.status,
                    local_services_verification_artifact.artifact_type,
                    local_services_verification_artifact.license_verification_artifact.license_type,
                    local_services_verification_artifact.license_verification_artifact.license_number,
                    local_services_verification_artifact.license_verification_artifact.licensee_first_name,
                    local_services_verification_artifact.license_verification_artifact.licensee_last_name,
                    local_services_verification_artifact.license_verification_artifact.rejection_reason,
                    local_services_verification_artifact.insurance_verification_artifact.insurance_type,
                    local_services_verification_artifact.insurance_verification_artifact.rejection_reason
                FROM local_services_verification_artifact
                {type_condition}
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            artifacts = []
            for row in response:
                artifact = row.local_services_verification_artifact
                artifacts.append({
                    'id': artifact.id,
                    'creation_time': artifact.creation_date_time,
                    'status': artifact.status,
                    'type': artifact.artifact_type,
                    'license_info': {
                        'type': artifact.license_verification_artifact.license_type,
                        'number': artifact.license_verification_artifact.license_number,
                        'first_name': artifact.license_verification_artifact.licensee_first_name,
                        'last_name': artifact.license_verification_artifact.licensee_last_name,
                        'rejection_reason': artifact.license_verification_artifact.rejection_reason
                    } if artifact.artifact_type == 'LICENSE' else None,
                    'insurance_info': {
                        'type': artifact.insurance_verification_artifact.insurance_type,
                        'rejection_reason': artifact.insurance_verification_artifact.rejection_reason
                    } if artifact.artifact_type == 'INSURANCE' else None
                })
            
            return artifacts
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_employees(self, customer_id):
        """Get information about Local Services employees."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    local_services_employee.status,
                    local_services_employee.type,
                    local_services_employee.university_degrees,
                    local_services_employee.residencies,
                    local_services_employee.fellowships,
                    local_services_employee.job_title,
                    local_services_employee.year_started_practicing,
                    local_services_employee.languages_spoken,
                    local_services_employee.first_name,
                    local_services_employee.middle_name,
                    local_services_employee.last_name
                FROM local_services_employee
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            employees = []
            for row in response:
                employee = row.local_services_employee
                employees.append({
                    'status': employee.status,
                    'type': employee.type,
                    'degrees': employee.university_degrees,
                    'residencies': employee.residencies,
                    'fellowships': employee.fellowships,
                    'job_title': employee.job_title,
                    'year_started': employee.year_started_practicing,
                    'languages': employee.languages_spoken,
                    'first_name': employee.first_name,
                    'middle_name': employee.middle_name,
                    'last_name': employee.last_name
                })
            
            return employees
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_campaign_performance(self, customer_id, start_date=None, end_date=None):
        """Get detailed campaign performance metrics."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            date_range = ""
            if start_date and end_date:
                date_range = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"
            
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.average_cpc,
                    metrics.ctr,
                    metrics.average_cost,
                    metrics.cost_per_conversion,
                    segments.date,
                    campaign.optimization_score,
                    campaign.bidding_strategy_type,
                    campaign.target_cpa.target_cpa_micros,
                    campaign.local_services_campaign_settings.category_bids
                FROM campaign
                WHERE campaign.advertising_channel_type = 'LOCAL_SERVICES'
                {date_range}
                ORDER BY segments.date DESC
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            performance_data = []
            for row in response:
                campaign = row.campaign
                metrics = row.metrics
                segments = row.segments
                
                performance_data.append({
                    'campaign_id': campaign.id,
                    'campaign_name': campaign.name,
                    'status': campaign.status,
                    'date': segments.date,
                    'metrics': {
                        'impressions': metrics.impressions,
                        'clicks': metrics.clicks,
                        'cost': metrics.cost_micros / 1000000,
                        'conversions': metrics.conversions,
                        'conversion_value': metrics.conversions_value,
                        'avg_cpc': metrics.average_cpc / 1000000,
                        'ctr': metrics.ctr,
                        'avg_cost': metrics.average_cost / 1000000,
                        'cost_per_conversion': metrics.cost_per_conversion / 1000000 if metrics.conversions > 0 else 0
                    },
                    'optimization_score': campaign.optimization_score,
                    'bidding_strategy': campaign.bidding_strategy_type,
                    'target_cpa': campaign.target_cpa.target_cpa_micros / 1000000 if campaign.target_cpa else None,
                    'category_bids': campaign.local_services_campaign_settings.category_bids
                })
            
            return performance_data
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_lead_insights(self, customer_id, start_date=None, end_date=None):
        """Get comprehensive lead insights including trends and patterns."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            date_range = ""
            if start_date and end_date:
                date_range = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"
            
            query = f"""
                SELECT
                    local_services_lead.lead_type,
                    local_services_lead.category_id,
                    local_services_lead.service_id,
                    local_services_lead.lead_status,
                    local_services_lead.lead_charged,
                    local_services_lead.credit_details.credit_state,
                    segments.date,
                    segments.hour,
                    segments.day_of_week,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    customer.local_services_settings.granular_license_statuses,
                    customer.local_services_settings.granular_insurance_statuses
                FROM local_services_lead
                WHERE 1=1 {date_range}
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            leads_data = []
            for row in response:
                lead = row.local_services_lead
                segments = row.segments
                metrics = row.metrics
                customer = row.customer
                
                leads_data.append({
                    'lead_info': {
                        'type': lead.lead_type,
                        'category': lead.category_id,
                        'service': lead.service_id,
                        'status': lead.lead_status,
                        'charged': lead.lead_charged,
                        'credit_state': lead.credit_details.credit_state
                    },
                    'timing': {
                        'date': segments.date,
                        'hour': segments.hour,
                        'day_of_week': segments.day_of_week
                    },
                    'metrics': {
                        'cost': metrics.cost_micros / 1000000,
                        'conversions': metrics.conversions,
                        'conversion_value': metrics.conversions_value
                    },
                    'verification_status': {
                        'license_status': customer.local_services_settings.granular_license_statuses,
                        'insurance_status': customer.local_services_settings.granular_insurance_statuses
                    }
                })
            
            return leads_data
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_geographic_performance(self, customer_id, start_date=None, end_date=None):
        """Get geographic performance data for Local Services campaigns."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            date_range = ""
            if start_date and end_date:
                date_range = f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'"
            
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    location_view.location_name,
                    location_view.targeting_location_type,
                    geographic_view.country_criterion_id,
                    geographic_view.location_type,
                    geographic_view.canonical_name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value
                FROM geographic_view
                WHERE campaign.advertising_channel_type = 'LOCAL_SERVICES'
                {date_range}
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            geo_data = []
            for row in response:
                campaign = row.campaign
                location = row.location_view
                geo_view = row.geographic_view
                metrics = row.metrics
                
                geo_data.append({
                    'campaign': {
                        'id': campaign.id,
                        'name': campaign.name
                    },
                    'location': {
                        'name': location.location_name,
                        'targeting_type': location.targeting_location_type,
                        'country_id': geo_view.country_criterion_id,
                        'location_type': geo_view.location_type,
                        'canonical_name': geo_view.canonical_name
                    },
                    'metrics': {
                        'impressions': metrics.impressions,
                        'clicks': metrics.clicks,
                        'cost': metrics.cost_micros / 1000000,
                        'conversions': metrics.conversions,
                        'conversion_value': metrics.conversions_value
                    }
                })
            
            return geo_data
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def get_competitor_insights(self, customer_id):
        """Get competitive insights and market position data."""
        if not self.is_initialized():
            raise Exception("Client is not initialized")
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.optimization_score,
                    campaign.optimization_score_weight,
                    campaign.bidding_strategy_type,
                    campaign.target_cpa.target_cpa_micros,
                    campaign.local_services_campaign_settings.category_bids,
                    metrics.search_impression_share,
                    metrics.search_rank_lost_impression_share,
                    metrics.search_budget_lost_impression_share,
                    metrics.average_cpc,
                    metrics.ctr,
                    metrics.conversions,
                    metrics.conversion_rate
                FROM campaign
                WHERE campaign.advertising_channel_type = 'LOCAL_SERVICES'
            """
            
            response = ga_service.search(customer_id=customer_id, query=query)
            
            competitor_data = []
            for row in response:
                campaign = row.campaign
                metrics = row.metrics
                
                competitor_data.append({
                    'campaign_info': {
                        'id': campaign.id,
                        'name': campaign.name,
                        'optimization_score': campaign.optimization_score,
                        'optimization_weight': campaign.optimization_score_weight,
                        'bidding_strategy': campaign.bidding_strategy_type,
                        'target_cpa': campaign.target_cpa.target_cpa_micros / 1000000 if campaign.target_cpa else None,
                        'category_bids': campaign.local_services_campaign_settings.category_bids
                    },
                    'market_metrics': {
                        'impression_share': metrics.search_impression_share,
                        'rank_lost_share': metrics.search_rank_lost_impression_share,
                        'budget_lost_share': metrics.search_budget_lost_impression_share,
                        'avg_cpc': metrics.average_cpc / 1000000,
                        'ctr': metrics.ctr,
                        'conversions': metrics.conversions,
                        'conversion_rate': metrics.conversion_rate
                    }
                })
            
            return competitor_data
            
        except GoogleAdsException as ex:
            self._handle_error(ex)

    def _build_date_condition(self, query_type, start_date=None, end_date=None):
        """Build date condition for query based on query type."""
        today = datetime.now().date()
        
        if query_type == 'custom' and start_date and end_date:
            return f"lead.creation_date_time BETWEEN '{start_date}' AND '{end_date}'"
        
        date_ranges = {
            'today': (today, today),
            'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
            'this_week': (today - timedelta(days=today.weekday()), today),
            'this_month': (today.replace(day=1), today)
        }
        
        if query_type in date_ranges:
            start, end = date_ranges[query_type]
            return f"lead.creation_date_time BETWEEN '{start}' AND '{end}'"
            
        return "TRUE"  # Default to no date filtering

    def _calculate_statistics(self, leads):
        """Calculate various statistics from lead data."""
        if not leads:
            return {}
            
        df = pd.DataFrame(leads)
        
        stats = {
            'total_leads': len(leads),
            'total_cost': df['cost'].sum(),
            'total_conversions': df['conversions'].sum(),
            'lead_types': df['type'].value_counts().to_dict(),
            'lead_status': df['status'].value_counts().to_dict(),
            'categories': df['category'].value_counts().to_dict(),
            'credit_states': df['credit_state'].value_counts().to_dict()
        }
        
        if stats['total_leads'] > 0:
            stats['avg_cost_per_lead'] = stats['total_cost'] / stats['total_leads']
            stats['conversion_rate'] = (stats['total_conversions'] / stats['total_leads']) * 100
        
        return stats

    def _handle_error(self, ex):
        """Handle Google Ads API exceptions."""
        error_message = []
        
        for error in ex.failure.errors:
            error_message.append(f"Error: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    error_message.append(f"\tField: {field_path_element.field_name}")
        
        raise Exception(' '.join(error_message))
