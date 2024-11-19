from smse_backend.app import create_app, db

app = create_app()


def main():
    # Ensure database is created
    with app.app_context():
        db.create_all()

    # Run the application
    app.run(debug=True)


if __name__ == "__main__":
    main()
