import os
import yaml
from flask import session

class ConfigManager:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'google-ads.yaml')
        
    def save_credentials(self, credentials):
        """Save API credentials to YAML file."""
        os.makedirs(self.config_dir, exist_ok=True)
        
        config = {
            'developer_token': credentials.get('developer_token'),
            'client_id': credentials.get('client_id'),
            'client_secret': credentials.get('client_secret'),
            'refresh_token': credentials.get('refresh_token'),
            'use_proto_plus': True,
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
    def load_credentials(self):
        """Load API credentials from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None
            
    def has_valid_credentials(self):
        """Check if valid credentials exist."""
        creds = self.load_credentials()
        if not creds:
            return False
            
        required_fields = ['developer_token', 'client_id', 'client_secret', 'refresh_token']
        return all(creds.get(field) for field in required_fields)
        
    def clear_credentials(self):
        """Remove existing credentials."""
        try:
            os.remove(self.config_file)
        except FileNotFoundError:
            pass
