#!/usr/bin/env python3
# Minimal API for CHATTY demo: /health and /api/command
from flask import Flask, request, jsonify
import os, time, subprocess

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status":"ok","time": int(time.time())})

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json() or {}
    cmd = data.get('command','')
    # Very small simulated router — replace with real agent calls
    if 'call' in cmd.lower():
        result = {"status":"ok","action":"call","message":"Would dial via Wazo (simulated)"}
    elif 'weather' in cmd.lower():
        result = {"status":"ok","action":"weather","message":"Binghamton: 42°F, cloudy (simulated)"}
    else:
        result = {"status":"ok","action":"default","message":"CHATTY simulated response for: "+cmd}
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('CHATTY_BACKEND_PORT', 8181))
    app.run(host='0.0.0.0', port=port)
