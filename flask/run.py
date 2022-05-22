import mimetypes

from app.backend import app


mimetypes.add_type('application/javascript', '.js')


def main():
    app.run(debug=True, host="localhost", port=5000)


if __name__ == '__main__':
    main()
