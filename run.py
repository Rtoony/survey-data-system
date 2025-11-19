"""
Application Entry Point
Run the Flask application using the Application Factory pattern
"""
import os
import sys
import importlib.util

# Import the factory from the app package
from app import create_app

# Create application instance using the factory
app = create_app()

# Make the app instance available to the legacy module
sys.modules['__main__'].app = app

# Import legacy routes from app.py using importlib to avoid naming conflict
# This registers all @app.route decorators onto our app instance
spec = importlib.util.spec_from_file_location("legacy_routes", "app.py")
legacy_routes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_routes_module)

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Run the application
    app.run(host=host, port=port, debug=debug)
