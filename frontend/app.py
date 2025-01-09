from flask import Flask, redirect, url_for, session, request, jsonify, Response, stream_with_context
from flask_oauthlib.client import OAuth
from dotenv import load_dotenv
import os
import subprocess
import requests
import json
import sys

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# OAuth setup
oauth = OAuth(app)
github = oauth.remote_app(
    'github',
    consumer_key=os.getenv("GITHUB_CLIENT_ID"),
    consumer_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    request_token_params={
        'scope': 'user:email',
    },
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
)

# Routes
@app.route('/')
def index():
    if 'github_token' in session:
        return '<a href="/logout">Logout</a>'
    return '<a href="/login">Login with GitHub</a>'

@app.route('/login')
def login():
    return github.authorize(callback="http://portable-auguste:5000/callback")

@app.route('/logout')
def logout():
    session.pop('github_token', None)
    return redirect(url_for('index'))

@app.route('/callback')
def authorized():
    response = github.authorized_response()
    if response is None or 'access_token' not in response:
        return 'Access denied: reason={} error={}'.format(
            request.args.get('error_reason'),
            request.args.get('error_description')
        )
    session['github_token'] = (response['access_token'], '')
    username = get_username()

    with open("users.json", "a") as f:
        if username in open("users.json").read():
            return redirect(url_for('frontend'))
        if "phoquiche" in username:
            f.write(json.dumps({"username": username, "role": "admin"}) + "\n")
        else:
            f.write(json.dumps({"username": username, "role": "user"}) + "\n")
    return redirect(url_for('frontend'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def get_username():
    token = get_github_oauth_token()[0]
    headers = {'Authorization': f'token {token}'}
    user_info = requests.get("https://api.github.com/user", headers=headers)
    userdata = user_info.json()
    return userdata['login']

def get_role(username):
    with open("users.json", "r") as f:
        for line in f:
            user = json.loads(line)
            if user["username"] == username:
                return user["role"]
    return None

# Real-time process streaming
@app.route('/process_stream', methods=['GET'])
def process_stream():
    if session.get('github_token') is None:
        return jsonify({"status": "error", "error": "Not authenticated"}), 401

    def generate():
        try:
            process = subprocess.Popen(
                ["python", "/home/cicd/PCS/main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(process.stdout)
            print(process.stderr)
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    yield f"data: {output.strip()}\n\n"  # Server-sent event format
            yield "data: Process completed.\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

# Frontend
@app.route('/index', methods=['GET'])
def frontend():
    if session.get('github_token') is None:
        return index()

    return '''
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('test').addEventListener('click', function(e) {
                e.preventDefault();
                document.getElementById('test').style.display = 'none';

                const outputElement = document.getElementById('output');
                outputElement.innerHTML = "<p>Streaming output...</p>";

                const eventSource = new EventSource('/process_stream');

                eventSource.onmessage = function(event) {
                    const data = event.data;
                    const pre = document.createElement("pre");
                    pre.textContent = data;
                    outputElement.appendChild(pre);
                    outputElement.scrollTop = outputElement.scrollHeight; // Auto-scroll
                };

                eventSource.onerror = function() {
                    outputElement.innerHTML += `<pre style="color: red;">Error: Connection lost or process completed.</pre>`;
                    eventSource.close();
                };

                return false;
            });
        });
    </script>

    <div class='container'>
        <h3>CI/CD Project</h3>
        <form>
            <a href="#" id="test"><button class='btn btn-default' type="button">Launch Deployment Pipeline</button></a>
        </form>
        <div id="output" style="margin-top: 20px; font-family: monospace; height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;"></div>
    </div>
    '''

@app.route('/page_dadmin_supersecret', methods=['GET'])
def admin_page():
    if session.get('github_token') is None:
        return index()
    username = get_username()
    role = get_role(username)
    if role == "admin":
        return '''
        <h1>Admin Page</h1>
        <p>You are an admin.</p>
        <form>
            <a href="#" id="test"><button class='btn btn-default' type="button">Delete the Library App</button></a>
        </form>
        '''
    else:
        return '''
        <h1>ALERT</h1>
        <p>You are not an admin.</p>
        '''

if __name__ == '__main__':
    app.run(debug=True)
