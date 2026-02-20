from flask import Flask, request, jsonify
from flask_cors import CORS
from embedding import get_embedding

app = Flask(__name__)
CORS(app)

@app.route('/embed', methods=['POST'])
def embed():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'text is required'}), 400
    
    embedding = get_embedding(text)
    return jsonify({'embedding': embedding})

if __name__ == '__main__':
    print("Starting embedding server on port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False)
