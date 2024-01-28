from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/message', methods=['POST'])
def process_message():
    content = request.json.get('content')
    conversation_id = request.json.get('conversation_id', 'default_id')  # Default value if not provided

    if not content:
        return jsonify({"error": "Content is required"}), 400

    # Process the content and conversation_id here
    # For example, just returning them
    return jsonify({
        "content": content,
        "conversation_id": conversation_id
    })

if __name__ == '__main__':
    app.run(debug=True)