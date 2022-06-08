""""Call client"""
import argparse
from src.Client import Client


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--host",
        type=str,
        help = "host of client's daemon",
        default = "localhost"
    )

    parser.add_argument(
        "--port",
        type = int,
        help = "port of client's daemon",
        default = 5000
    )

    args = parser.parse_args()


    client = Client(args.host, args.port)
    client.run()
    
