from flask import Flask

def create_app():
    app = Flask(__name__)
    #For Security Misconfigs
    app.config['DEBUG'] = True  #Vulnerable to exposing sensitive information
    app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production
    
    # Initialize database setup
    from app.database import init_db
    init_db()

    #Routes
    from app.routes import main
    app.register_blueprint(main)
    return app
