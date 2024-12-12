from models.app import App
from utils.utils import *


def main():
    service = authenticate()
    if service is None:
        return
    
    app = App(service)
    app.run()

if __name__ == '__main__':
    main()

