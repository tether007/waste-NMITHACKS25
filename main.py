import os
from app import app
from routes import register_routes
from auth import auth_bp

# Configure the upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Register auth blueprint
app.register_blueprint(auth_bp)

# Register all routes
register_routes(app)

if __name__ == "__main__":
    # Determine if we're running in production or development
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app with appropriate settings
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=not is_prod
    )
