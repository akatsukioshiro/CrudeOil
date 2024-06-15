from crudeoil import CrudeOil, render_template, response

app = CrudeOil(__name__)

@app.route('/', methods=["GET"])
def home():
    template_args = {
        "greeting": "Hello All!, How are You ?"
    }
    return render_template("index.html", mime='text/html', status_code=200, template_args=template_args)
	
@app.route('/dashboard', methods=["GET"])
def home():
    return response("<body>Bye</body>", mime='text/html', status_code=200)

@app.route('/get_args_test', methods=["GET"])
def home():
    return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
