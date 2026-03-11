from flask import Flask, request, jsonify

app = Flask(__name__)
registry = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    service = data['service']
    address = data['address']

    registry.setdefault(service, []).append(address)

    return {"status": "registered"}

@app.route('/discover/<service>')
def discover(service):
    return jsonify(registry.get(service, []))

app.run(port=5001)

# Made with Bob
