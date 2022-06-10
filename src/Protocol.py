import pickle
import socket

class Protocol:
    """Functions to create and encode messages"""

    @classmethod
    def msg_first_connect(cls, node_type, recv_host, recv_port):
        """ Connect message """
        msg = pickle.dumps({"type": "first_connect", "node_type": node_type, "recv_host": recv_host, "recv_port": recv_port})
        return msg
        

    @classmethod
    def msg_connect_ack(cls, nodes : list, general_map: dict):
        """ Send neighbours message """
        msg = pickle.dumps({"type": "connect_ack", "nodes": nodes, "general_map": general_map})
        return msg



    @classmethod
    def msg_connect(cls, node_type, recv_host, recv_port):
        """ Connect message """
        msg = pickle.dumps({"type": "connect", "node_type": node_type, "recv_host": recv_host, "recv_port": recv_port})
        return msg


    @classmethod
    def msg_request_image_list(cls):
        msg = pickle.dumps({"type": "request_list"})
        return msg


    @classmethod
    def msg_image_list(cls, image_list):
        msg = pickle.dumps({"type": "image_list", "image_list": image_list})
        return msg


    @classmethod
    def msg_request_image(cls, hashkey):
        msg = pickle.dumps({"type": "request", "hashkey": hashkey})
        return msg


    @classmethod
    def msg_image(cls, hashkey, image):
        msg = pickle.dumps({"type": "image", "hashkey": hashkey, "image": image})
        return msg

    
    @classmethod
    def msg_update(cls, update):
        msg = pickle.dumps({"type": "update", "update": update})
        return msg




    @classmethod
    def msg_debug(cls):
        msg = pickle.dumps({"type": "debug"})
        return msg






    """ Send and receive messages """

    @classmethod
    def send_msg(cls, msg, sock: socket):
        try:
            msg_size = len(msg).to_bytes(2, "big")
            msg_to_send = msg_size + msg
            sock.send(msg_to_send)
        except Exception as e:
            print(e)

    @classmethod
    def receive_msg(cls, sock : socket):
        try:
            msg_size= int.from_bytes(sock.recv(2), "big")
            if msg_size != 0:
                msg = sock.recv(msg_size)
                return pickle.loads(msg)
        except Exception as e:
            print(e)
        return None


