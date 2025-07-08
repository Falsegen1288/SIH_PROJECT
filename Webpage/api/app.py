from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os, uuid
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# Important: Proper CORS setup
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)



# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.sih_project

results_coll = db.results
uploads_coll = db.uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/results', methods=['GET'])
def get_results():
    results = list(results_coll.find({}, {'_id': 1, 'name': 1, 'buy': 1, 'sell': 1}))
    for r in results:
        r['_id'] = str(r['_id'])
    return jsonify(results), 200

@app.route('/post-result', methods=['POST'])
def post_result():
    data = request.json
    name = data.get('name')
    buy = data.get('buy')
    sell = data.get('sell')
    if not name:
        return jsonify({'error': 'Dataset name required'}), 400
    result = {'name': name, 'buy': buy, 'sell': sell}
    results_coll.insert_one(result)
    return jsonify({'status': 'added'}), 200

@app.route('/delete-result/<rid>', methods=['DELETE'])
def delete_result(rid):
    results_coll.delete_one({'_id': ObjectId(rid)})
    return jsonify({'status': 'deleted'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = f"{uuid.uuid4().hex}.csv"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    uploads_coll.insert_one({'filename': filename, 'path': path})
    return jsonify({'status': 'success', 'filename': filename}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
