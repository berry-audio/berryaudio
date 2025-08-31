from setuptools import setup

setup(
    name="berryaudio",
    version="0.1",
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "berryaudio = main:main",
        ],
    },
)
