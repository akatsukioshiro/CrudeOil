from crudeoil import CrudeOil, render_template, response

app = CrudeOil(__name__)

@app.route('/r0', methods=["GET"])
def home(request):
    name = request.args.get("name", "no-name-entered")
    template_args = {
        "greeting": f"Hello {name}!, How are You ?"
    }
    return render_template("index.html", mime='text/html', status_code=200, template_args=template_args)
	
@app.route('/r1', methods=["POST"])
def home(request):
    name = request.body.get("name", "no-name-entered")
    return response(f"<body>Bye {name}</body>", mime='text/html', status_code=200)

@app.route('/r2', methods=["GET", "POST"])
def home(request):
    if request.headers.get("method") == "GET":
        return "GET request received"
    elif request.headers.get("method") == "POST":
        return "POST request received"
    else:
        return "not GET or POST"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
