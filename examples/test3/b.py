import json

a = """
POST /post_args_test HTTP/1.1
Content-Type: text/plain
User-Agent: PostmanRuntime/7.32.2
Accept: */*
Cache-Control: no-cache
Postman-Token: 879d2556-9065-4689-b636-95bcd562dcc4
Host: localhost:9090
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Content-Length: 18

{
    "a": "b"
}
"""

def _request_json(raw_request):
    request = {}
    raw_headers, body = a.split("\n\n")
    headers = {}
    headers["method"], headers["route"], headers["protocol"] = raw_headers.strip().split("\n")[0].split(" ")
    for line in raw_headers.strip().split("\n")[1:]:
        if line.strip() == "":
            continue
        key = line.split(": ")[0]
        val = line.split(": ")[1]
        print(key)
        print(val)
        headers[key] = val
    request["headers"] = headers
    request["body"] = json.loads(body)
    return request

print(_request_json(a))
