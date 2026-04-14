import socket
import os
import ssl

"""
WHAT I THINK THIS IS DOING (im in over my head ;-;)
NO REDIRECTS:
    -main takes 2 inputs, the desired host and path
    -main then calls fetch to to pass arguements to status, headers, body
    -fetch sets port to 80, use_ssl variable to False and sets up a redirect loop
    -while redirect is less than the set max:
    -creates variable called plug and assigns it the connect function which takes the inputted host and set port/use_ssl arguments
    -connect assigns socket object to be variable "plug", sets timeout to 5 seconds
    -TRICKY: it then uses the connect method from socket and passes it a host and port to begin 3 way handshake with
    -sends an binary encoded request in HTTP/1.1 to the passed host/path on port 80
    -recieves response as encoded binary file in 4096 chunks
    -closes the plug socket object ending the connecton
    -decodes the response in utf-8 and ignores errors
    -splits decoded response into 2 objects: the raw header and the html body
    -splits the raw header and grabs a third object, the status line
    -splits the status line and and creates status code using just the numerical status
    -creates headers dictionary and sorts raw header into it
    -returns status code, header dicitonary and body objects to fetch
    -fetch checks the status code and if its not a redirect it returns it to main
    -main then prints the status code, the server from the headers dictionary, and a preview of the body
    -it then saves the body to a new or existing txt file in fetched folder using the save body function
REDIRECTS:
    -if the first parse response returns status code 301-303 or 307-308
    -checks headers dicitonary's location key, if it starts with https:// or // it sets port to 443 and use ssl to true
    -it then removes the https:// or http:// from the start of the location value
    -splits the new location value by first / and grabs whats on the right, and then appends it to path
    -if theres nothing to append it sets host to the new location and path to root
    -adds 1 to the redirects 
    -if redirects isnt at max, while loop starts again with refreshed values, this time with port as 443 and use ssl as True
    -since use ssl is True now, it creates a variable called context thats an ssl encoding
    -it then wraps plug with this encoding and returns it to fetch
    -send this new request to the updated host/path
    -if the new response is a redirect status code it repeats this up to 5 times with the new locations given
    -else it prints the status of the port, what the server is (as long as status is 200(OK)), and the header preview
    -and saves the body text to a txt file in fetched folder
"""

def main():
    while True:
    #tries to connect to host
        try:
            input_host = get_host()
            input_path = get_path()
            status, headers, body = fetch(input_host, input_path)

            #prints recieved data
            print(f"Status         : {status}")
            print(f"Server         : {headers.get('server')}")     
            print(f"Body preview   : {body[:200]}")       
            save_body(body, input_host, input_path)
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


#grabs host and sets port to 80, added use_ssl
def connect(host, port=80, use_ssl=False):
    #connects to host and returns connected socket object "plug" which is connected to port 80 of host
    plug = socket.socket()
    plug.settimeout(5)
    #socket.connect needs a tuple, hence the extra ()
    plug.connect((host, port))

    if use_ssl:
        context = ssl.create_default_context()
        plug = context.wrap_socket(plug, server_hostname=host)
    return plug


#sends request to host webpage
def send_req(plug, host, path="/"):
    #sends binary request to host in HTTP/1.1 for webpage, ensures connection ends once data recieved
    #----------------NEW, USER-AGENT HEADER-------------------------------
    ask = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36\r\n"
        f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
        "Connection: close\r\n\r\n"
    )
    #----------------------------------------------------------------------
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

    print(f"RAW STATUS LINE: '{status_line}'")
    status_code = status_line.split(" ")[1]
    print(f"PARSED STATUS: '{status_code}'")
    #creates dictionary to store header info in
    header_dict = {}
    for line in headers_raw.split("\r\n")[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            #makes all dict keys lowercase
            header_dict[key.lower()] = value

    return status_code, header_dict, body


#grabs host and sets path to default to "/"
def fetch(host, path="/"):
    MAX_REDIRECTS = 5
    redirects = 0
    port = 80
    use_ssl = False

    while redirects < MAX_REDIRECTS:
        #opens connection
        plug = connect(host, port, use_ssl)
        #sends request to connection
        send_req(plug, host, path)
        #recieves binary response
        response = receive_response(plug)
        #closes connection
        plug.close()

        #unpacks the tuple returned by parse_response into three separate variables
        status, headers, body = parse_response(response)

        #checks status of recieved decoded binary file, if a redirect it passes to to location
        if status in ("301", "302", "303", "307", "308"):


            #grabs location name from headers dict
            location = headers.get("location")
            #if theres no location it breaks
            if not location:
                break

            print(f"REDIRECTING TO {location}")
            print(f"PORT = {port}, use_ssl = {use_ssl} ")
#--------------------NEW----------------------------------------
            #checks if location is an https and if so sets port to 443 and use_ssl to True
            if location.startswith("https://") or location.startswith("//"):
                port = 443
                use_ssl = True
            else:
                port = 80
                use_ssl = False
#---------------------------------------------------------------


            #removes prefix from http or https url
            location = location.replace("https://", "").replace("http://", "")
            if "/" in location:
                #on the first / in location, it splits it adds the second index(path) to the grander path variable
                host, path = location.split("/", 1)
                path = "/" + path
                
            else:
                #otherwise if theres no / host becomes current location
                host = location
                #and path becomes root
                path = "/"
            
            #adds 1 to the redirect tally
            redirects += 1
        
        #if not a redirect status breaks the loop
        else:
            break
    
    if redirects == MAX_REDIRECTS:
        print("MAXIMUM REDIRECTS")
    
    return status, headers, body


def save_body(body, host, input_path):
    folder = "fetched"
    #creates/looks for fetched folder. exists_ok=True prevents crash if folder already exists
    os.makedirs(folder, exist_ok=True)

    #makes name savable by replacing . and / with _
    filename = host.replace(".", "_") + input_path.replace("/", "_") + ".txt"
    #adds filename to folder
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
        f.write(body)
    print(f"CHECK BODY AT: {filepath}")

    #TO FIX: save html files in a better way, also add path to filename in order to distinguish between saved data


if __name__ == "__main__":
    main()