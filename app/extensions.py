"""
Flask Extensions
Initialize extensions without binding to app instance
"""
from flask_cors import CORS
from flask_caching import Cache

# Initialize extensions without app binding
# These will be bound in the application factory
cors = CORS()
cache = Cache()
