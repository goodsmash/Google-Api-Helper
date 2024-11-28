import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import app

def main():
    """Main function to run the application."""
    try:
        # Get port from environment or use default
        port = int(os.getenv('PORT', 5000))
        
        # Run the application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True
        )
    
    except Exception as e:
        print(f"Error starting the application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
