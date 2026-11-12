"""Ponto de entrada do Confia+.

Execute com `python apli.py` ou `flask --app apli run`.
As rotas ficam organizadas no pacote `routes`.
"""
import os

from core import app, initialize_database, IS_PRODUCTION

# Importar os módulos registra suas rotas no aplicativo Flask.
from routes import auth, profile, shopping, operations, admin  # noqa: F401,E402


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
        and not IS_PRODUCTION
    )
