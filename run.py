import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    print(f"\n" + "="*50)
    print(f"  Budget Buddy is starting!")
    print(f"  Access the app at: http://127.0.0.1:{port}")
    print(f"  or:                http://localhost:{port}")
    print(f"="*50 + "\n")
    app.run(debug=True, host=host, port=port)
