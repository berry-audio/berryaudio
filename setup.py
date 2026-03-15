from setuptools import setup

with open("version.py") as f:
    exec(f.read())

setup(
    name="berryaudio",
    version=__version__,
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "berryaudio = main:main",
        ],
    },
)
