from smse_backend import create_app, db
from sqlalchemy import text
from sqlalchemy import event
from pgvector.psycopg2 import register_vector

app = create_app()


def main():
    # Ensure database is created
    with app.app_context():
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        db.create_all()

    # Run the application
    app.run(debug=True)


if __name__ == "__main__":
    main()
