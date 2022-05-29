""""Call daemon"""
from src.Daemon import Daemon

if __name__ == "__main__":
    client = Daemon()
    client.run()
