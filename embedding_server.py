from flask import Flask, request, jsonify
from flask_cors import CORS
from embedding import get_embedding
from rag_pipeline import rag_query

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

@app.route('/rag', methods=['POST'])
def rag():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'query is required'}), 400
    
    result = rag_query(query)
    return jsonify(result)

if __name__ == '__main__':
    print("Starting embedding and RAG server on port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False)
