# Ensure numpy is present even if a cached Railway build skipped requirements.txt
web: python -m pip install -q "numpy==2.2.6" && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
