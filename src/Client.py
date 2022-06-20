import fcntl
import os
import sys
import socket
import selectors
from .Protocol import Protocol as P
from PIL import Image

class Client:
    
    def __init__(self, daemon_host, daemon_port):
        """Initializes client."""

        self.canceled = False
        self.daemon_host = daemon_host
        self.daemon_port = daemon_port
        self.s_info = None
        self.node_type = "client"

        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        #socket and selector
        self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #connect to daemon
        self.s.connect((self.daemon_host, self.daemon_port))
        self.s_info = self.s.getsockname()
        connect_msg = P.msg_connect(self.node_type, self.s_info[0], self.s_info[1])
        P.send_msg(connect_msg, self.s)

        #register objects
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        self.sel.register(self.s, selectors.EVENT_READ, self.read)



    def read(self, sock, mask):
        msg = P.receive_msg(sock)

        if msg:
            msg_type = msg["type"]

            if msg_type == "image_list":
                img_lst = msg["image_list"]
                
                print("\n======= Images on network =======")
                for img in img_lst:
                    print(img)
                print("===================================")


            elif msg_type == "debug_ack":

                general_map = msg["general_map"]
                all_nodes = msg["all_nodes"]
                storage = msg["storage"]

                print("\nDEBUG\n")
                for item in sorted(general_map.items()):
                    print(item)
                for item in sorted(storage.items()):
                    print(item)
                for item in sorted(all_nodes):
                    print(item)

            elif msg_type == "image":
                img_hash = msg["hashkey"]
                img = msg["image"]

                #show image
                img.show()

            elif msg_type == "request_ack":
                img = msg["image"]

                if img:
                    print("img recv")
                    img.show()
                else:
                    print("Something went wrong")

            else:
                print("ALERT: unknow message received!")


        else:

            self.sel.unregister(sock)
            sock.close()
            print("Connection closed")




    def got_keyboard_data(self, stdin, mask):
        print()
        print(">> ", end="", flush=True)
        
        client_input = stdin.read().strip()
        
        #print("User input: ", client_input)

        if len(client_input) == 0:
            return

        elif client_input == "log out":
            self.canceled = False
        
        elif client_input == "list":
            request_msg = P.msg_request_image_list()
            P.send_msg(request_msg, self.s)
            
            print("List request message has been sent!")

        elif client_input == "debug":
            request_debug = P.msg_debug()
            P.send_msg(request_debug, self.s)
            
            print("Debug request message has been sent!")


        elif len(client_input.split()) == 1 and len(client_input) == 16:   #request image
            request_img_msg = P.msg_request_image(client_input)
            P.send_msg(request_img_msg, self.s)
        
        else:
            print("ERROR: command not found!")

        

    def run(self):
        """Run client"""

        while not self.canceled:
            for key, mask in self.sel.select():
                callback = key.data
                callback(key.fileobj, mask)

        print("Closing connection with daemon...")
        self.sel.unregister(self.s)
        self.sel.unregister(sys.stdin)
        self.sel.close()
        print("Connection closed.")
