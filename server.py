from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import logging
from browser_agent import BrowserAgent
import os
from threading import Thread

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global browser agent instance
browser_agent = None

def init_browser_agent():
    """Initialize the browser agent in a separate thread."""
    global browser_agent
    try:
        logger.info("Initializing browser agent...")
        browser_agent = BrowserAgent(
            ollama_url="http://localhost:11434",
            model="dolphin-llama3:8b-256k"
        )
        logger.info("Browser agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize browser agent: {e}")

@app.route('/')
def index():
    """Serve the dashboard."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/execute-task', methods=['POST'])
async def execute_task():
    """Execute a task using the browser agent."""
    try:
        data = request.get_json()
        task = data.get('task', '')
        mode = data.get('mode', 'autonomous')
        
        if not task:
            return jsonify({
                'success': False,
                'error': 'No task provided'
            }), 400
        
        if browser_agent is None:
            return jsonify({
                'success': False,
                'error': 'Browser agent not initialized'
            }), 503
        
        logger.info(f"Executing task in {mode} mode: {task}")
        
        # Execute the task
        result = await browser_agent.execute_task(task)
        
        return jsonify({
            'success': True,
            'result': result,
            'task': task,
            'mode': mode
        })
        
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the browser agent."""
    return jsonify({
        'browser_agent_ready': browser_agent is not None,
        'ollama_connected': True if browser_agent else False
    })

@app.route('/api/stop', methods=['POST'])
async def stop_task():
    """Stop the current task."""
    try:
        if browser_agent:
            await browser_agent.stop()
            return jsonify({
                'success': True,
                'message': 'Task stopped'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Browser agent not initialized'
            }), 503
    except Exception as e:
        logger.error(f"Error stopping task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize browser agent in a separate thread
    init_thread = Thread(target=init_browser_agent)
    init_thread.start()
    
    # Run Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
