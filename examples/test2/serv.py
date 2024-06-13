from crudeoil import CrudeOil, render_template, response
import time
import subprocess

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
    stop_message = "data: STOP\n\n"
    yield stop_message.encode('utf-8')
    time.sleep(1)

@app.sse('/events_cli', methods=["GET"])
def events_cli():
    # Example CLI command to run
    command = ["ping", "-c", "25", "localhost"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True)

    for line in iter(process.stdout.readline, ''):
        data = f"data: {line.strip()}\n\n"
        yield data.encode('utf-8')
        
    process.stdout.close()
    process.wait()
        
    stop_message = "data: STOP\n\n"
    yield stop_message.encode('utf-8')
    time.sleep(1)

@app.route('/sse_test', methods=["GET"])
def home():
    template_args = {
        "greeting": "Hello All!, How are You ?"
    }
    return render_template("sse_page.html", mime='text/html', status_code=200, template_args=template_args)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
