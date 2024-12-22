from smse_backend import create_app

app = create_app()


def main():
    # Run the application
    app.run()


if __name__ == "__main__":
    main()
