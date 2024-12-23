from os import environ
from smse_backend import create_app

config_name = environ.get("FLASK_ENV", "DevelopmentConfig")

print(f" * Running with config: {config_name}")

app = create_app(config_name)


def main():
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
