from flask import Flask, render_template, request, jsonify, session
import requests
import os

app = Flask(__name__)
# Secret key for secure login sessions
app.secret_key = os.environ.get('SECRET_KEY', 'default_cyber_secret_123')

# Admin Credentials & API Keys
ADMIN_USER = os.environ.get('ADMIN_USER', 'cyber')
ADMIN_PASS = os.environ.get('ADMIN_PASS', '1948s')
ADDY_API_KEY = os.environ.get('ADDY_API_KEY')
ADDY_API_BASE = 'https://app.addy.io/api/v1'

REQ_TIMEOUT = 10  

def is_admin():
    return session.get('logged_in') is True

def get_addy_headers():
    # X-Requested-With prevents Addy.io from returning HTML error pages
    return {
        "Authorization": f"Bearer {ADDY_API_KEY}",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }

@app.route('/')
def index():
    return render_template('index.html')

# --- Admin Auth Routes ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == ADMIN_USER and data.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({"success": True})

@app.route('/api/auth/status')
def auth_status():
    return jsonify({"logged_in": is_admin()})

# --- Addy.io Alias Management Routes ---

@app.route('/api/aliases', methods=['GET'])
def get_aliases():
    if not is_admin(): return jsonify({"error": "Unauthorized"}), 401
    try:
        res = requests.get(f"{ADDY_API_BASE}/aliases", headers=get_addy_headers(), timeout=REQ_TIMEOUT)
        if not res.ok:
            return jsonify({"error": f"Addy API Error: {res.status_code}"}), res.status_code
            
        return jsonify(res.json().get('data', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/aliases', methods=['POST'])
def generate_alias():
    if not is_admin(): return jsonify({"error": "Unauthorized"}), 401
    
    # We must explicitly tell Addy which domain and format to use
    payload = {
        "domain": "anonaddy.me",
        "format": "random_characters",
        "description": "Generated via Private Render Dashboard"
    }
    
    try:
        res = requests.post(f"{ADDY_API_BASE}/aliases", json=payload, headers=get_addy_headers(), timeout=REQ_TIMEOUT)
        
        # Safer error handling: If Addy rejects it, grab the exact reason why
        if not res.ok:
            error_msg = "Unknown Error"
            try:
                error_msg = res.json().get('message', res.text)
            except:
                error_msg = res.text
            return jsonify({"error": f"Addy.io rejected request: {error_msg}"}), res.status_code
            
        return jsonify(res.json().get('data', {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/aliases/<alias_id>', methods=['DELETE'])
def delete_alias(alias_id):
    if not is_admin(): return jsonify({"error": "Unauthorized"}), 401
    try:
        res = requests.delete(f"{ADDY_API_BASE}/aliases/{alias_id}", headers=get_addy_headers(), timeout=REQ_TIMEOUT)
        if not res.ok:
            return jsonify({"error": f"Failed to delete: {res.status_code}"}), res.status_code
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
