#!/usr/bin/env python3
"""
Minimale Guardrail Proxy voor Ollama
Blokkeert alleen echt illegale content, laat de rest door.
"""

import re
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Minimale blacklist - alleen echt illegale categorieën
ILLEGAL_PATTERNS = [
    # Child abuse
    r'\b(csam|child\s*porn|cp\s*links|pedo|lolita\s*porn)\b',
    # Terrorism
    r'\b(bomb\s*making|terrorist\s*attack\s*plan|jihad\s*instructions)\b',
    # Doxxing
    r'\b(doxxing|dox\s*someone|real\s*home\s*address\s*of|swatting)\b',
]

# Log alle requests (voor audit)
REQUEST_LOG = []

def log_request(user_content, blocked=False, reason=None):
    """Log alle requests voor audit trail"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'content_preview': user_content[:200],
        'blocked': blocked,
        'reason': reason
    }
    REQUEST_LOG.append(log_entry)
    
    # Keep last 1000 entries
    if len(REQUEST_LOG) > 1000:
        REQUEST_LOG.pop(0)
    
    if blocked:
        logging.warning(f"BLOCKED: {reason} - Preview: {user_content[:100]}")
    else:
        logging.info(f"ALLOWED: {user_content[:100]}")

def check_content(text):
    """
    Check of content illegaal is.
    Returns: (is_safe, reason_if_blocked)
    """
    text_lower = text.lower()
    
    for pattern in ILLEGAL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, f"Blocked: pattern matched - {pattern}"
    
    return True, None

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_chat_completions():
    """Proxy voor Ollama chat completions API"""
    try:
        data = request.json
        
        # Extract user content
        messages = data.get('messages', [])
        user_content = ' '.join([
            m.get('content', '') 
            for m in messages 
            if m.get('role') == 'user'
        ])
        
        # Check content
        is_safe, reason = check_content(user_content)
        log_request(user_content, blocked=not is_safe, reason=reason)
        
        if not is_safe:
            return jsonify({
                'error': {
                    'message': 'Content blocked by guardrail proxy',
                    'type': 'content_policy_violation',
                    'code': 'content_blocked'
                }
            }), 403
        
        # Forward to Ollama
        ollama_url = 'http://localhost:11434/v1/chat/completions'
        response = requests.post(ollama_url, json=data, stream=data.get('stream', False))
        
        if data.get('stream'):
            # Pass through streaming response
            return response.raw.read(), response.status_code, response.headers.items()
        else:
            return response.json(), response.status_code
    
    except Exception as e:
        logging.error(f"Proxy error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def proxy_models():
    """Proxy voor Ollama models API"""
    try:
        response = requests.get('http://localhost:11434/v1/models')
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ollama_connected': check_ollama_connection(),
        'requests_logged': len(REQUEST_LOG)
    })

@app.route('/stats', methods=['GET'])
def stats():
    """Get proxy statistics"""
    blocked_count = sum(1 for log in REQUEST_LOG if log['blocked'])
    return jsonify({
        'total_requests': len(REQUEST_LOG),
        'blocked_requests': blocked_count,
        'allowed_requests': len(REQUEST_LOG) - blocked_count,
        'recent_logs': REQUEST_LOG[-10:]  # Last 10
    })

def check_ollama_connection():
    """Check if Ollama is running"""
    try:
        response = requests.get('http://localhost:11434/v1/models', timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    print("="*60)
    print("Guardrail Proxy Starting...")
    print("="*60)
    print("Listening on: http://localhost:11435")
    print("Forwarding to: http://localhost:11434 (Ollama)")
    print("")
    print("Minimal guardrails active:")
    for pattern in ILLEGAL_PATTERNS:
        print(f"  - {pattern}")
    print("="*60)
    
    # Check Ollama connection
    if check_ollama_connection():
        print("✓ Ollama is running")
    else:
        print("⚠ Warning: Ollama not detected on port 11434")
        print("  Start Ollama with: ollama serve")
    
    print("="*60)
    app.run(host='0.0.0.0', port=11435, debug=False)
