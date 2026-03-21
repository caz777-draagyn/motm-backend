# Quick Start Guide - Match Engine Test Bench

## Step 1: Install Dependencies (if needed)

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
```

Or if you're using a virtual environment:

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Start the FastAPI Server

Run the following command in your terminal from the project root directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**What this does:**
- `uvicorn` - The ASGI server that runs FastAPI
- `main:app` - Points to the `app` object in `main.py`
- `--reload` - Auto-reloads server when code changes (useful for development)
- `--host 0.0.0.0` - Makes server accessible from any network interface
- `--port 8000` - Runs on port 8000

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Access the Test Bench UI

Open your web browser and navigate to:

```
http://localhost:8000/api/test-bench/
```

Or if accessing from another machine on your network:

```
http://YOUR_IP_ADDRESS:8000/api/test-bench/
```

## Step 4: Using the Test Bench

1. **Configure Teams:**
   - Set team names in the header inputs
   - For each player:
     - Enter player name
     - Select position (GK for goalkeeper, others for outfield)
     - Set attribute values (0-20 range)

2. **Set Simulation Parameters:**
   - Select number of matches (1, 10, 100, or 1000)
   - Set match length in minutes (default: 90)

3. **Run Simulation:**
   - Click "Run Simulation" button
   - Wait for results (may take a moment for large match counts)

4. **View Results:**
   - Match summary (wins/draws, average goals)
   - Team statistics
   - Player statistics with skill usage

## Alternative: Using the API Directly

You can also use the API endpoints directly:

### Single Match Simulation
```bash
POST http://localhost:8000/api/match-engine/simulate
Content-Type: application/json

{
    "home_team": {
        "name": "Home Team",
        "players": [...]
    },
    "away_team": {
        "name": "Away Team",
        "players": [...]
    },
    "minutes": 90
}
```

### Get Constants
```bash
GET http://localhost:8000/api/match-engine/constants
```

### Batch Simulation
```bash
POST http://localhost:8000/api/test-bench/simulate
Content-Type: application/json

{
    "home_team": {...},
    "away_team": {...},
    "num_matches": 100,
    "minutes": 90
}
```

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, use a different port:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
Then access at `http://localhost:8001/api/test-bench/`

### Database Connection Error
If you get database errors, make sure your `DATABASE_URL` environment variable is set. For testing the match engine only, you might want to temporarily comment out the database initialization in `main.py`.

### Module Not Found
Make sure you're running from the project root directory and all dependencies are installed.

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.
