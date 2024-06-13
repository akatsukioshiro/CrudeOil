from crudeoil import CrudeOil, render_template, response
import time

app = CrudeOil(__name__)

@app.sse('/events', methods=["GET"])
def the_event():
    c = 5
    while True:
        if c == 0:
            break
        data = f"data: Hello, client! The time is {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        yield data.encode('utf-8')
        time.sleep(5)
        c-=1

@app.route('/', methods=["GET"])
def home():
    template_args = {
        "greeting": "Hello All!, How are You ?"
    }
    return render_template("index.html", mime='text/html', status_code=200, template_args=template_args)
	
@app.route('/dashboard', methods=["GET"])
def home():
    return response("<body>Bye</body>", mime='text/html', status_code=200)

@app.route('/sse_test', methods=["GET"])
def home():
    template_args = {
        "greeting": "Hello All!, How are You ?"
    }
    return render_template("sse_page.html", mime='text/html', status_code=200, template_args=template_args)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
