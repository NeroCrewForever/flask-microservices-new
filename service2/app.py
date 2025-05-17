from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', other_service_url='http://service1.default.svc.cluster.local')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)