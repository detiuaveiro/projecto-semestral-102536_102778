""""Call daemon"""
import argparse
from src.Daemon import Daemon

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--folder",
        type=str,
        help = "images folder path",
        default = "."
    )

    # ======================= FOR NOW =======================
    
    parser.add_argument(
        "--host",
        type=str,
        help = "daemon host",
        default = "localhost"
    )

    
    parser.add_argument(
        "--port",
        type=int,
        help = "daemon port",
        default = 5000
    )

    # =======================================================

    args = parser.parse_args()


    client = Daemon(args.host, args.port, args.folder)
    client.run()
