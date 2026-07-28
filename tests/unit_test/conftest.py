from backend.config import Config


def pytest_configure():
    Config.SECRET_KEY = "qNlzuFq0XlLGSFmM2i3F7kgiu_69mwKvp8tEmshm8oY"
