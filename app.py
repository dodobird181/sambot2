from flask import Flask, request, jsonify, Response, stream_with_context, render_template
import time

app = Flask(__name__)

@app.route('/stream_response', methods=['POST'])
def stream_response():

    content = request.json.get('content')
    conversation_id = request.json.get('conversation_id', 'default_id')

    if not content:
        return jsonify({"error": "content is required"}), 400

    # Process the content and conversation_id here
    # For example, just returning them
    return jsonify({
        "content": content,
        "conversation_id": conversation_id
    })


@app.route('/stream')
def stream_html():
    def generate_html():
        for i in range(1, 6):  # Example: 5 chunks of HTML content
            #yield f"<div><p>Chunk {i} of HTML content</p></div>"
            yield f"data: <div><h3>Chunk {i} of HTML content</h3></div>\n\n"
            time.sleep(1)  # Simulate delay
        yield f'data: STOP\n\n'

    return Response(stream_with_context(generate_html()), mimetype='text/event-stream')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)