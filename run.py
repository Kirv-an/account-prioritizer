"""Application entry point"""

from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    print("=" * 60)
    print("Account Prioritization & Research Tool")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(debug=True, host='127.0.0.1', port=5001)