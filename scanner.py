import socket
import os

def main():
    while True:
    #tries to connect to host
        try:
            input_host = get_host()
            status, headers, body = fetch(input_host, get_path())


            #prints recieved data
            print(f"Status         : {status}")
            print(f"Server         : {headers.get('Server')}")            
            save_body(body, input_host)
            
            break
        #if no host is found, prints error
        except Exception as e:
            print(f"\nCONNECTION FAILED: {e}\n")
            if input("PRESS Y TO TRY AGAIN ").strip().lower() != "y":
                print("GOODBYE")
                break


#gets and error checks host url
def get_host():
    while True:
        host = input("HTTP ADDRESS? ").replace("https://", "").replace("http://", "").strip()
        host = host.strip("/")

        if not host:
            print("\nPLEASE ENTER AND ADDRESS\n")
            continue

        if "." not in host:
            print("\nError: INVALID ADDRESS, NO PERIOD\n")
            continue

        if " " in host:
            print("\nError: NO SPACES ALLOWED\n")
            continue
        return host
        
def get_path():
    path = input("PATH? (press enter for root): ").strip()
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    
    return path

#grabs host and sets port to 80
def connect(host, port=80):
    #connects to host and returns connected socket object "plug" which is connected to port 80 of host
    plug = socket.socket()
    plug.settimeout(5)
    #socket.connect needs a tuple, hence the extra ()
    plug.connect((host, port))
    return plug

#sends request to host webpage
def send_req(plug, host, path="/"):
    #sends binary request to host in HTTP/1.1 for webpage, ensures connection ends once data recieved
    ask = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    plug.send(ask.encode())

#recieves response from http connection from "plug"
def receive_response(plug):
    response = b""
    while True:
        chunk = plug.recv(4096)
        if not chunk:
            break
        response += chunk
    return response

#takes response and decodes it
def parse_response(response):
    #decodes response in charset utf-8 and splits the raw header from the body
    decoded = response.decode("utf-8", errors="ignore")
    headers_raw, body = decoded.split("\r\n\r\n", 1)

    #grabs the status of the connection and splits it from status code, 200 == OK
    status_line = headers_raw.split("\r\n")[0]
    status_code = status_line.split(" ")[1]

    #creates dictionary to store header info in
    header_dict = {}
    for line in headers_raw.split("\r\n")[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            header_dict[key] = value

    return status_code, header_dict, body

#grabs host and sets path to default to "/"
def fetch(host, path="/"):
    #opens connection
    plug = connect(host)
    #sends request to connection
    send_req(plug, host, path)
    #recieves binary response
    response = receive_response(plug)
    #closes connection
    plug.close()

    #unpacks the tuple returned by parse_response into three separate variables
    status, headers, body = parse_response(response)
    return status, headers, body

def save_body(body, host):
    folder = "fetched"
    #creates/looks for fetched folder. exists_ok=True prevents crash if folder already exists
    os.makedirs(folder, exist_ok=True)

    #makes name savable by replacing . and / with _
    filename = host.replace(".", "_").replace("/", "_") + ".txt"
    #adds filename to folder
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
        f.write(body)
    print(f"CHECK BODY AT: {filepath}")

    #TO FIX: save html files in a better way, also add path to filename in order to distinguish between saved data


if __name__ == "__main__":
    main()