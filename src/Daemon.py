import socket
# from PIL import Image
# import imagehash
# import glob

import Functions


class Daemon:
    """Daemon -> Node"""

    def __init__(self, host, port, folder_path):
        self.HOST= host
        self.PORT= port
        self.FOLDER_PATH= folder_path

        self.my_img_list= {}

        pass

    

    def run(self):
        pass