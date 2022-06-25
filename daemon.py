""""Call daemon"""
import argparse
from src.Daemon_ import Daemon

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--folder",
        type=str,
        help = "images folder path",
        default = "."
    )

    args = parser.parse_args()


    client = Daemon(args.folder)
    client.run()
