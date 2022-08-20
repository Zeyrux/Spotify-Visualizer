import mimetypes

from app.backend import App

mimetypes.add_type("application/javascript", ".js")
app = App().app
app.env = "development"
#socket_io = SocketIO(app.app)
#socket_io.run(app.app, host="localhost", port=5000, debug=True)
