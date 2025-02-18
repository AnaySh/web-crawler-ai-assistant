from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db, shutdown_session
from services import AIService, DatabaseService
from models import Provider, Model, APIKey
from config import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def create_app():
    with app.app_context():
        init_db()
    return app

create_app()

@app.teardown_appcontext
def cleanup(resp_or_exc):
    shutdown_session()

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "endpoints": [
            {"path": "/ask", "method": "POST", "description": "Ask a question about webpage content"},
            {"path": "/save", "method": "POST", "description": "Save a Q&A pair"},
            {"path": "/saved", "method": "GET", "description": "Get saved Q&A pairs for a webpage"},
            {"path": "/delete", "method": "POST", "description": "Delete a saved Q&A pair"},
            {"path": "/update_api_key", "method": "POST", "description": "Update OpenAI API key"},
            {"path": "/get_api_key", "method": "GET", "description": "Get stored OpenAI API key"}
        ]
    })

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    if not data or 'question' not in data or 'webpage_content' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    provider = data.get('provider', 'openai')  # Default to OpenAI if not specified
    model = data.get('model')  # Use the model from API key if not specified
    
    response = AIService.ask_question(
        question=data['question'],
        context=data['webpage_content'],
        provider=provider,
        model=model,
        user_id=data.get('user_id')  # Optional user_id
    )
    
    if "error" in response:
        return jsonify(response), 400
    return jsonify(response)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    if not all(k in data for k in ['webpage_url', 'question', 'answer']):
        return jsonify({"error": "Missing required fields"}), 400

    result = DatabaseService.save_qa_pair(
        webpage_url=data['webpage_url'],
        question=data['question'],
        answer=data['answer'],
        context=data.get('context'),
        created_by=data.get('user_id')  # Optional user_id
    )
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/saved', methods=['GET'])
def get_saved():
    webpage_url = request.args.get('webpage_url')
    if not webpage_url:
        return jsonify({"error": "Missing webpage_url parameter"}), 400

    result = DatabaseService.get_qa_pairs(webpage_url)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    return jsonify({"qa_pairs": result})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.json
    if 'id' not in data:
        return jsonify({"error": "Missing id field"}), 400

    result = DatabaseService.delete_qa_pair(data['id'])
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/update_api_key', methods=['POST'])
def update_api_key():
    data = request.json
    required_fields = ['key', 'provider', 'model']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields. Required: {required_fields}"}), 400

    result = DatabaseService.update_api_key(
        key=data['key'],
        provider=data['provider'],
        model=data['model'],
        user_id=data.get('user_id')  # Optional user_id
    )
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/get_api_key', methods=['GET'])
def get_api_key():
    provider = request.args.get('provider')
    user_id = request.args.get('user_id')
    
    if not provider:
        return jsonify({"error": "Provider parameter is required"}), 400
        
    if provider not in [p.value for p in Provider]:
        return jsonify({"error": f"Invalid provider. Must be one of: {[p.value for p in Provider]}"}), 400

    # Query the database for the key
    query = APIKey.query.filter_by(provider=provider, is_valid=True)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    api_key = query.first()
    
    if api_key:
        return jsonify({
            "key": api_key.key,
            "provider": api_key.provider,
            "model": api_key.model,
            "user_id": api_key.user_id
        })
    return jsonify({"error": f"No valid API key found for provider: {provider}"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51034)
