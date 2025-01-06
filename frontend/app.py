from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from dotenv import load_dotenv
import os

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
        user_info = github.get('user')
        return jsonify(user_info.data)
    return '<a href="/login">Login with GitHub</a>'

@app.route('/login')
def login():
    return github.authorize(callback="http://127.0.0.1:5000/callback")

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
    user_info = github.get('user')
    return jsonify(user_info.data)

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.route('/process', methods=['GET'])
def process_data():
    os.system("/opt/homebrew/bin/python3.11 ../main.py")
    return jsonify({"status": "success"})

@app.route('/index',methods=['GET'])
def frontend():
  if session.get('github_token') is None:
    return redirect(url_for('login'))

  return '''<script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
<script type=text/javascript>
        $(function() {
          $('a#test').on('click', function(e) {
            e.preventDefault()
            $.getJSON('/process',
                function(data) {
              //do nothing
            });
            return false;
          });
        });
</script>


<div class='container'>
    <h3>Test</h3>
        <form>
            <a href=# id=test><button class='btn btn-default'>Test</button></a>
        </form>

</div>'''

if __name__ == '__main__':
    app.run(debug=True)



