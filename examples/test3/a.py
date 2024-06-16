import json

def get_request_var_dict(request_args):
    request_var_dict = {}
    start = 0
    key = ""
    curr_closing = ""
    closings = { "'": "'", '"': '"', "(": ")", "{": "}", "[": "]", "<": ">", "`": "`" }
    for index in range(len(request_args)):
        #print(request_args[index], curr_closing)
        if request_args[index] == "=" and curr_closing == "":
            key = request_args[start:index]
            #print(key)
            start = index+1
        elif request_args[index] == "&" and key != "" and curr_closing == "":
            request_var_dict[key] = request_args[start:index]
            key=""
            start = index+1
        elif request_args[index] in closings and curr_closing == "":
            if request_args[index-1] == "=":
                curr_closing = request_args[index]
        elif curr_closing != "":
            if request_args[index] == closings[curr_closing]:
                request_var_dict[key] = request_args[start:index+1]
                key=""
                start = index+1
                curr_closing = ""
    if key != "":
        request_var_dict[key] = request_args[start:len(request_args)]
        key=""
    if "" in request_var_dict:
        request_var_dict.pop("")
    return json.dumps(request_var_dict)




#print(get_request_var_dict('env=SE29,SE24&abc="a&b=c"&dict={"a":"b"}&choose=aaa'))
print(get_request_var_dict('env=SE29,SE24&seenv=SE24&a=0'))
