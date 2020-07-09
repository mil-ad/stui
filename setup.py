from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

setup(
    name="stui",
    description="A Slurm client for the terminal.",
    long_description="A Slurm client for the terminal.", #TODO: Use readme
    version="0.1.0",
    packages=find_packages(),
    author="Milad Alizadeh",
    url="https://github.com/mi-lad/stui",
    keywords=["slurm", "cluster"],
    author_email="m@mil.ad",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=["urwid", "fabric"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["stui=stui.stui:main",]},
)
