import fcntl
import os
import sys
import socket
import selectors
from traceback import print_tb
from urllib.request import urlcleanup
from .Protocol import Protocol as P

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
                
                print("======= Images on network =======")
                for img in img_lst:
                    print(img)
                print("=================================")

            else:
                print("ALERT: unknow message received!")


        else:

            self.sel.unregister(sock)
            sock.close()

            #find my new central node (could be me!)
            if sock in self.all_socks.values() and sock == self.all_socks[self.central_node]:
                self.central_node = self.find_central_node()
                print("New central node: ", self.central_node)

            #remove socket from all_socks
            if sock in self.all_socks.values():
                self.remove_node(sock)



    def got_keyboard_data(self, stdin, mask):
        sys.stdout.write(">> ")
        sys.stdout.flush()
        
        client_input = stdin.read().strip()
        print("Input: ", client_input)
        
        #print("User input: ", client_input)

        if len(client_input) == 0:
            return

        elif client_input == "log out":
            self.canceled = False
        
        elif client_input == "list":
            request_msg = P.msg_request_image_list()
            P.send_msg(request_msg, self.s)
            
            print("List request message has been sent!")
        
        else:
            print("bruh")

        

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
