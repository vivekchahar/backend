"""
Circular Waste Intelligence System - Flask Web Application
Main entry point: Upload images → AI prediction → Data logging → Live dashboard
Extended with: Smart Bins monitoring + Route Optimization
"""

import os
import sys

# Ensure project root is in the path (for bin_simulator / route_optimizer imports)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ─── App Setup ──────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for frontend API calls
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

CSV_FILE = 'data.csv'
CSV_COLUMNS = ['timestamp', 'waste_type', 'confidence', 'location']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── Download AI model if missing ──────────────────────────
MODEL_FILE = os.path.join(os.getcwd(), 'waste_classifier.keras')

print("Checking model path:", MODEL_FILE)
print("File exists:", os.path.exists(MODEL_FILE))

if not os.path.exists(MODEL_FILE):
    print("⬇️ Downloading model from Google Drive...")
    try:
        import gdown

        file_id = "1C_fSkb8Ej0tO-XPxhFPNVVwxf09uMjfr"
        url = f"https://drive.google.com/uc?id={file_id}&confirm=t"

        gdown.download(url, MODEL_FILE, quiet=False)

        print("✅ Model downloaded successfully!")

    except Exception as e:
        print(f"❌ Download failed: {e}")

# ─── Import AI model (loads once) ──────────────────────────
try:
    from utils.waste_classifier import predict as classify_waste
except Exception as e:
    print(f"⚠️ Warning: Could not load waste_classifier (Model might be missing): {e}")
    def classify_waste(filepath):
        return {
            'class': 'unknown',
            'display_name': 'Unknown (Model Missing)',
            'confidence': 0.0,
            'action': 'Model file is missing or failed to load',
            'all_predictions': {}
        }

# ─── Import Smart Bin + Route modules ──────────────────────
from bin_simulator import (
    load_bins, simulate_tick, update_bin_from_scan,
    collect_bin, get_bin_stats, initialize_bins, DEPOT
)
from route_optimizer import optimize_route


# ─── Helpers ────────────────────────────────────────────────
def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_csv():
    """Create CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)


def log_prediction(waste_type, confidence, location='Unknown'):
    """Append a prediction entry to the CSV file."""
    ensure_csv()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, waste_type, confidence, location])


def read_predictions():
    """Read all predictions from CSV. Returns list of dicts."""
    ensure_csv()
    entries = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def get_analytics():
    """Compute dashboard analytics from logged data."""
    entries = read_predictions()
    total = len(entries)

    if total == 0:
        return {
            'total': 0,
            'counts': {},
            'percentages': {},
            'recent': [],
        }

    # Count each waste type
    counts = {}
    for e in entries:
        wt = e.get('waste_type', 'unknown')
        counts[wt] = counts.get(wt, 0) + 1

    # Calculate percentages
    percentages = {k: round(v / total * 100, 1) for k, v in counts.items()}

    # Recent entries (last 10, newest first)
    recent = list(reversed(entries[-10:]))

    return {
        'total': total,
        'counts': counts,
        'percentages': percentages,
        'recent': recent,
    }


@app.route('/')
def index():
    return jsonify({"status": "Circular Waste Intelligence API is alive and running!"})


@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload, run AI prediction, log result, update bins."""
    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save uploaded file
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"waste_{timestamp_str}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Run AI classification
    result = classify_waste(filepath)

    # Get optional location from form
    location = request.form.get('location', '').strip() or 'Unknown'
    result['location'] = location

    # Log to CSV
    log_prediction(result['class'], result['confidence'], location)
    
    # Ensure 'label' and 'confidence' are explicitly in response as requested
    result['label'] = result['class']

    # ── Integration: Update nearest smart bin ──
    updated_bin = update_bin_from_scan(result['class'], location)
    result['updated_bin'] = updated_bin

    # Add image path for display
    result['image_url'] = '/' + filepath.replace('\\', '/')

    # JSON response for the frontend
    return jsonify(result)


@app.route('/dashboard-data')
def dashboard_data():
    """API endpoint returning analytics as JSON for Chart.js."""
    analytics = get_analytics()
    return jsonify(analytics)


# ═══════════════════════════════════════════════════════════
#  SMART BINS + ROUTE OPTIMIZATION ROUTES
# ═══════════════════════════════════════════════════════════

@app.route('/optimize')
def optimize():
    """Compute optimized collection route (called from main page button)."""
    result = optimize_route()
    return jsonify(result)


# The original /bins page has been removed. Use /api/bins API instead.


@app.route('/api/bins')
def api_bins():
    """JSON API: Get all bin data."""
    bins = load_bins()
    stats = get_bin_stats()
    return jsonify({'bins': bins, 'stats': stats, 'depot': DEPOT})


@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """Simulate one IoT tick — increase fill levels."""
    bins = simulate_tick()
    stats = get_bin_stats()
    return jsonify({'bins': bins, 'stats': stats, 'message': 'Simulation tick complete'})


@app.route('/api/route')
def api_route():
    """Compute optimized collection route."""
    result = optimize_route()
    return jsonify(result)


@app.route('/api/collect', methods=['POST'])
def api_collect():
    """Mark a bin as collected (reset fill level)."""
    data = request.get_json()
    bin_id = data.get('bin_id', '')
    if bin_id:
        bins = collect_bin(bin_id)
        return jsonify({'success': True, 'bins': bins})
    return jsonify({'success': False, 'error': 'No bin_id provided'})


@app.route('/api/reset-bins', methods=['POST'])
def api_reset_bins():
    """Reset all bins to fresh random state."""
    bins = initialize_bins()
    stats = get_bin_stats()
    return jsonify({'bins': bins, 'stats': stats, 'message': 'Bins reset'})


# ─── Run ────────────────────────────────────────────────────
if __name__ == '__main__':
    ensure_csv()
    # Ensure bins are initialized
    load_bins()
    print("\n" + "=" * 55)
    print("  🌿 Circular Waste Intelligence API")
    print("  🚀 Backend API  → http://0.0.0.0:10000")
    print("=" * 55 + "\n")
    app.run(host="0.0.0.0", port=10000)
