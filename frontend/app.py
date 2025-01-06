from flask import Flask, request, jsonify
import os


app = Flask(__name__)

@app.route('/process', methods=['GET'])
def process_data():
    os.system("/opt/homebrew/bin/python3.11 ../main.py")
    return jsonify({"status": "success"})

@app.route('/index',methods=['GET'])
def frontend():
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



