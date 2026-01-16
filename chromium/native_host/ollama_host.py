#!/usr/bin/env python3
"""
No-Guardrail AI - Native Messaging Host
Bridge tussen Chromium browser en lokale Ollama instance
"""

import sys
import json
import struct
import requests
import logging
from typing import Dict, Any

# Configuration
OLLAMA_URL = 'http://localhost:11434'
DEFAULT_MODEL = 'dolphin-uncensored'
LOG_FILE = '/tmp/ollama_host.log'

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_message(message: Dict[str, Any]) -> None:
    """
    Send a message to the browser via stdout.
    Native messaging protocol requires 4-byte length prefix.
    """
    encoded_message = json.dumps(message).encode('utf-8')
    message_length = len(encoded_message)
    
    # Write length (4 bytes, native byte order)
    sys.stdout.buffer.write(struct.pack('I', message_length))
    # Write message
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()
    
    logging.debug(f"Sent message: {message}")

def read_message() -> Dict[str, Any]:
    """
    Read a message from the browser via stdin.
    """
    # Read message length (4 bytes)
    text_length_bytes = sys.stdin.buffer.read(4)
    if len(text_length_bytes) == 0:
        sys.exit(0)
    
    text_length = struct.unpack('I', text_length_bytes)[0]
    
    # Read message
    text = sys.stdin.buffer.read(text_length).decode('utf-8')
    message = json.loads(text)
    
    logging.debug(f"Received message: {message}")
    return message

def call_ollama(prompt: str, model: str = DEFAULT_MODEL, 
                system: str = None, context: str = None) -> Dict[str, Any]:
    """
    Call Ollama API with the given prompt.
    """
    try:
        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nUser: {prompt}"
        
        payload = {
            'model': model,
            'prompt': full_prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'top_p': 0.9,
            }
        }
        
        if system:
            payload['system'] = system
        
        logging.info(f"Calling Ollama with model: {model}")
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'success': True,
            'response': result.get('response', ''),
            'model': model,
            'done': result.get('done', True)
        }
        
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to Ollama")
        return {
            'success': False,
            'error': 'Cannot connect to Ollama. Is it running?'
        }
    except requests.exceptions.Timeout:
        logging.error("Ollama request timed out")
        return {
            'success': False,
            'error': 'Request timed out'
        }
    except Exception as e:
        logging.error(f"Ollama error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def call_ollama_chat(messages: list, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Call Ollama chat API with message history.
    """
    try:
        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': 0.7,
            }
        }
        
        logging.info(f"Calling Ollama chat with {len(messages)} messages")
        response = requests.post(
            f'{OLLAMA_URL}/api/chat',
            json=payload,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'success': True,
            'message': result.get('message', {}),
            'model': model,
            'done': result.get('done', True)
        }
        
    except Exception as e:
        logging.error(f"Ollama chat error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def handle_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming message from browser.
    """
    msg_type = message.get('type', 'generate')
    model = message.get('model', DEFAULT_MODEL)
    
    if msg_type == 'generate':
        # Simple text generation
        prompt = message.get('prompt', '')
        context = message.get('context', None)
        system = message.get('system', None)
        
        return call_ollama(prompt, model, system, context)
        
    elif msg_type == 'chat':
        # Chat with message history
        messages = message.get('messages', [])
        return call_ollama_chat(messages, model)
        
    elif msg_type == 'ping':
        # Health check
        return {'success': True, 'pong': True}
        
    elif msg_type == 'models':
        # List available models
        try:
            response = requests.get(f'{OLLAMA_URL}/api/tags')
            response.raise_for_status()
            return {
                'success': True,
                'models': response.json().get('models', [])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    else:
        return {
            'success': False,
            'error': f'Unknown message type: {msg_type}'
        }

def main():
    """
    Main loop: read messages from browser, process, send response.
    """
    logging.info("Ollama Native Messaging Host started")
    
    try:
        while True:
            # Read message from browser
            message = read_message()
            
            # Process message
            response = handle_message(message)
            
            # Send response back to browser
            send_message(response)
            
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        send_message({
            'success': False,
            'error': f'Host error: {str(e)}'
        })

if __name__ == '__main__':
    main()
