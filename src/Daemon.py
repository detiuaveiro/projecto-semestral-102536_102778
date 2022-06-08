from functools import total_ordering
import socket
import selectors
import pickle
from .Protocol import Protocol as P


class Daemon:
    """Daemon -> Node"""


    def __init__(self, folder_path):
        self.canceled = False
        self.node_type = "daemon"
        self.central_node = self.find_central_node()
        self.host, self.port = self.get_addr()  # reveiving socket (endpoint)

        self.FOLDER_PATH= folder_path
        self.all_socks = {}    #{(host, port): socket}  -> daemon sockets
        self.img_map = {}
        self.client = None


        self.sel = selectors.DefaultSelector()

        # receiving socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen()

        print(f"Clients can connect via: {self.host} {self.port}")
        
        self.sel.register(self.s, selectors.EVENT_READ, self.verify)


        # connect to central daemon
        if self.port != self.central_node[1]:  #i'm not the central node

            self.all_socks[self.central_node] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.all_socks[self.central_node].connect(self.central_node)

            #connect to central node
            connect_msg = P.msg_connect(self.node_type, self.host, self.port)
            P.send_msg(connect_msg, self.all_socks[self.central_node])

            #register daemon socket
            self.sel.register(self.all_socks[self.central_node], selectors.EVENT_READ, self.read)


            print("-------------------")
            for n in self.all_socks.keys():
                print(n)
            print("-------------------")
                



    def verify(self, sock, mask):
        conn, addr = sock.accept()
        connect_msg = P.receive_msg(conn)

        if connect_msg:
            print("msg recv: ", connect_msg)
            host = connect_msg["recv_host"]
            port = connect_msg["recv_port"]
            node_type = connect_msg["node_type"] 

            if node_type == "daemon":
                print("DEAMON WANTS TO CONNECT")

                # send to my neighbour all the nodes i know
                nodes_msg = P.msg_nodes(list(self.all_socks.keys()))
                P.send_msg(nodes_msg, conn)
                
                #store the neighbour node
                self.all_socks[(host, port)] = sock

                print("-------------------")
                for n in self.all_socks.keys():
                    print(n)
                print("-------------------")
                

            if node_type == "client":
                print("CLIENT WANTS TO CONNECT")

                #store the node client
                self.client = conn

            
            # print(self.all_socks)
            self.sel.register(conn, selectors.EVENT_READ, self.read)




    def read(self, sock :socket, mask):
        
        msg = P.receive_msg(sock)

        if msg:
            msg_type = msg["type"]

            if msg_type == "nodes":
                nodes = msg["nodes"]  # array with neighbour nodes
                self.connect_to_nodes(nodes)

            elif msg_type == "request_list":
                request_msg = P.msg_image_list(["image1", "image2", "image3", "image4"])
                P.send_msg(request_msg, sock)

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




    def run(self):
        """ Run until canceled """

        while not self.canceled:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)   


    def connect_to_nodes(self, nodes):
        """ connect to other nodes """

        for n in nodes:
            if n not in self.all_socks:

                self.all_socks[n] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print("Connecting to ", n)
                self.all_socks[n].connect(n)

                #connect to node
                connect_msg = P.msg_connect(self.node_type, self.host, self.port)
                print("Connect to daemon port: ", n[1])
                P.send_msg(connect_msg, self.all_socks[n])

                #register daemon socket
                self.sel.register(self.all_socks[n], selectors.EVENT_READ, self.read)          

        
        print("-------------------")
        for n in self.all_socks.keys():
            print(n)
        print("-------------------")
                      



    def get_addr(self):
        """ Get a valid addr to use """

        host = "localhost"
        port = 5000   #start port

        while self.is_port_in_use(port):
            port += 1

        return (host, port)

    

    def find_central_node(self):
        """ Return the addr of an existing daemon node """

        host = 'localhost'
        port = 5000
        total_ports = 100  #total ports to check 5000 -> 5100

        for _ in range(total_ports):
            if self.is_port_in_use(port):
                print("There is already a node")
                break
            else:
                port += 1
        
        if port == 5100:  #if there is no centra node
            port = 5000
        
        # print("Central node: ", (host, port))
        return (host, port)  # return ('locahost', 5000) if there are no daemon nodes



    def is_port_in_use(self, port: int) -> bool:
        """ Check if port is in use """       

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    
    def remove_node(self, s):
        node_to_delete = None
        for node, sock in self.all_socks.items():
            if s == sock:
                node_to_delete = node
        
        #remove the node
        del self.all_socks[node_to_delete]