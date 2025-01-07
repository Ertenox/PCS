from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

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
    #go to frontend
    return redirect(url_for('frontend'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')



@app.route('/process', methods=['GET'])
def process_data():
    if session.get('github_token') is None:
        return jsonify({"status": "error", "error": "Not authenticated"}), 401
    try:
        os.chdir("..")
        # Run the external sc ipt and wait for it to complete
        result = subprocess.run(
            ["python", "main.py"],
            capture_output=True,
            text=True
        )
        
        # Log the output for debugging
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        
        # Return the result
        if result.returncode == 0:
            return jsonify({"status": "ok", "output": result.stdout.strip()})
        else:
            return jsonify({"status": "error", "error": result.stdout.strip()}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

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
                fetch('/process')
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);
                        const outputElement = document.getElementById('output');
                        outputElement.innerHTML = `<pre>${data.output}</pre>`;
                        outputElement.innerHTML += `<pre style="color: red;">${data.error}</pre>`;

                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('output').innerHTML = `<pre style="color: red;">Error fetching /process: ${error}</pre>`;
                    });

                return false;
            });
        });
    </script>

    <div class='container'>
        <h3>CI/CD Projet</h3>
        <form>
            <a href="#" id="test"><button class='btn btn-default' type="button">Lancer le pipeline de déploiement</button></a>
        </form>
        <div id="output" style="margin-top: 20px; font-family: monospace;"></div>
    </div>
    '''


if __name__ == '__main__':
    app.run(debug=True)



