from flask import Flask

from core.helpers import cleanup_generated
from core.routes import register_routes

app = Flask(__name__)

cleanup_generated()
register_routes(app)

if __name__ == "__main__":
    app.run(debug=False, port=5050)
