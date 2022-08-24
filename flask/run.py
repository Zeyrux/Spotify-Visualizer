import mimetypes

from app.app import app


if __name__ == "__main__":
    app.run(host="localhost", port=6000, debug=True)
