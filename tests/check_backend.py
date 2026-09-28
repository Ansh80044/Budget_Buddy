import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

results = {
    "env_file": {
        "status": "PASS",
        "details": {}
    },
    "flask": {
        "status": "PENDING",
        "details": ""
    },
    "supabase": {
        "status": "PENDING",
        "details": {}
    },
    "openai": {
        "status": "PENDING",
        "details": ""
    },
    "tesseract": {
        "status": "PENDING",
        "details": ""
    },
    "local_db": {
        "status": "PENDING",
        "details": ""
    }
}

# 1. Check ENV variables
supabase_url = os.environ.get('SUPABASE_URL', '').strip()
supabase_key = os.environ.get('SUPABASE_KEY', '').strip()
openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
flask_key = os.environ.get('FLASK_SECRET_KEY', '').strip()
tesseract_cmd = os.environ.get('TESSERACT_CMD', '').strip()

is_supabase_placeholder = not supabase_url or 'your-project' in supabase_url or 'your_supabase' in supabase_key
is_openai_placeholder = not openai_key or 'your_openai_api_key' in openai_key

results["env_file"]["details"] = {
    "supabase_url_configured": bool(supabase_url and not is_supabase_placeholder),
    "supabase_key_configured": bool(supabase_key and not is_supabase_placeholder),
    "openai_key_configured": bool(openai_key and not is_openai_placeholder),
    "flask_key_configured": bool(flask_key),
    "tesseract_configured": bool(tesseract_cmd)
}

# 2. Test Flask app initialization
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app import create_app
    app = create_app()
    with app.test_client() as client:
        res = client.get('/')
        if res.status_code in [200, 302]:
            results["flask"]["status"] = "PASS"
            results["flask"]["details"] = f"Flask app created successfully. Route '/' returned {res.status_code}."
        else:
            results["flask"]["status"] = "WARN"
            results["flask"]["details"] = f"Route '/' returned status code {res.status_code}."
except Exception as e:
    results["flask"]["status"] = "FAIL"
    results["flask"]["details"] = str(e)

# 3. Test Local SQLite DB
try:
    from app.services import local_db
    conn = local_db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    results["local_db"]["status"] = "PASS"
    results["local_db"]["details"] = f"Local SQLite functional with tables: {', '.join(tables)}"
except Exception as e:
    results["local_db"]["status"] = "FAIL"
    results["local_db"]["details"] = str(e)

# 4. Test Supabase
if is_supabase_placeholder:
    results["supabase"]["status"] = "NOT_CONFIGURED"
    results["supabase"]["details"] = "Placeholders still present in .env for SUPABASE_URL / SUPABASE_KEY."
else:
    if supabase_url.endswith('/rest/v1/'):
        results["supabase"]["status"] = "CONFIG_ERROR"
        results["supabase"]["details"] = "SUPABASE_URL has '/rest/v1/' at the end. Please remove it."
    else:
        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            
            # Check tables
            table_checks = {}
            for tbl in ['profiles', 'transactions', 'budgets', 'budget_categories', 'savings_goals']:
                try:
                    res = client.table(tbl).select('*').limit(1).execute()
                    table_checks[tbl] = "OK"
                except Exception as ex:
                    table_checks[tbl] = f"Error: {str(ex)[:100]}"
            
            all_ok = all(v == "OK" for v in table_checks.values())
            if all_ok:
                results["supabase"]["status"] = "PASS"
                results["supabase"]["details"] = "Connected successfully. All required tables exist and are reachable."
            else:
                results["supabase"]["status"] = "PARTIAL_OR_SCHEMA_MISSING"
                results["supabase"]["details"] = table_checks
        except Exception as e:
            results["supabase"]["status"] = "FAIL"
            results["supabase"]["details"] = str(e)

# 5. Test AI (Groq or OpenAI)
groq_key = os.environ.get('GROQ_API_KEY', '').strip()
openai_key = os.environ.get('OPENAI_API_KEY', '').strip()

if groq_key and not groq_key.startswith('your_'):
    try:
        from openai import OpenAI
        groq_client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        models = groq_client.models.list()
        results["openai"]["status"] = "PASS"
        results["openai"]["details"] = f"Groq Free AI authenticated successfully ({len(models.data)} models available)."
    except Exception as e:
        results["openai"]["status"] = "FAIL"
        results["openai"]["details"] = f"Groq error: {str(e)}"
elif openai_key and not is_openai_placeholder:
    try:
        from openai import OpenAI
        oai_client = OpenAI(api_key=openai_key)
        models = oai_client.models.list()
        results["openai"]["status"] = "PASS"
        results["openai"]["details"] = "OpenAI API key authenticated successfully."
    except Exception as e:
        results["openai"]["status"] = "FAIL"
        results["openai"]["details"] = str(e)
else:
    results["openai"]["status"] = "NOT_CONFIGURED"
    results["openai"]["details"] = "Neither GROQ_API_KEY nor OPENAI_API_KEY is configured."

# 6. Test Tesseract
try:
    from app.services.ocr_service import extract_text_from_image
    from PIL import Image, ImageDraw
    import io
    img = Image.new('RGB', (200, 50), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), 'TEST RECEIPT 123', fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    extracted = extract_text_from_image(buf.getvalue())
    if extracted:
        results["tesseract"]["status"] = "PASS"
        results["tesseract"]["details"] = f"Tesseract OCR installed & working. Sample extracted: '{extracted}'"
    else:
        results["tesseract"]["status"] = "WARN"
        results["tesseract"]["details"] = "Tesseract executed but extracted empty string."
except Exception as e:
    results["tesseract"]["status"] = "FAIL"
    results["tesseract"]["details"] = str(e)

print("===HEALTH_CHECK_RESULT===")
print(json.dumps(results, indent=2))
