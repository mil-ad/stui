import codecs
from setuptools import setup, find_packages
from stui import __version__

with codecs.open("README.md", encoding="utf-8") as f:
    README = f.read()

setup(
    name="stui",
    description="A Slurm client for the terminal",
    long_description=README,
    long_description_content_type="text/markdown",
    version=__version__,
    packages=find_packages(),
    author="Milad Alizadeh",
    url="https://github.com/mi-lad/stui",
    keywords=["slurm", "cluster"],
    author_email="m@mil.ad",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=["urwid", "fabric>=2.5.0"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["stui=stui.cli:cli",]},
)
