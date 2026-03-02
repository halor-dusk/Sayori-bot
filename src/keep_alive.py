# This file is only made for
# the render host

from flask import Flask
from threading import Thread
from envar import PORT

app = Flask(__name__) # Server

@app.route('/')
def home() -> str:
    return "Hello, I am alive!"


def run() -> None:
    app.run(host="0.0.0.0", port=PORT)


def keep_alive() -> None:
    t = Thread(target=run, daemon=True)
    t.start()