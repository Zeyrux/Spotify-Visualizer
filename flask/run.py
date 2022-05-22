import mimetypes

from app.backend import app

from flask_socketio import SocketIO


mimetypes.add_type('application/javascript', '.js')


def main():
    app.env = "development"
    socket_io = SocketIO(app)
    socket_io.run(app, host="localhost", port=5000)


if __name__ == '__main__':
    main()
