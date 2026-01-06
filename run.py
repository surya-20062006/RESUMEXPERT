import os
import sys
from app import app, init_db

def main():
    """Main function to run the application"""
    
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        os.environ['FLASK_ENV'] = 'development'
        app.config['DEBUG'] = True
        print("🚀 Starting ResumeXpert in Development Mode...")
    else:
        print("🚀 Starting ResumeXpert...")
    
    
    print("📊 Initializing database...")
    init_db()
    
    
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('generated_resumes', exist_ok=True)
    
    print("✅ Database initialized successfully!")
    print("🌐 Application will be available at: http://localhost:5000")
    print("📱 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config.get('DEBUG', False)
        )
    except KeyboardInterrupt:
        print("\n👋 ResumeXpert stopped successfully!")
    except Exception as e:
        print(f"❌ Error starting ResumeXpert: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
