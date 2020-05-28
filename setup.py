from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

packages=find_packages()
print(packages)

setup(
    name="slurmtop",
    description="A terminal-based graphical activity monitor for Slurm",
    long_description=readme,
    version="0.1",
    packages=find_packages("src"),
    author="Milad Alizadeh",
    url="https://github.com/mi-lad/slurmtop",
    keywords=["slurm", "cluster"],
    author_email="milad@mil.ad",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License"
    ],
    install_requires=["urwid"],
    python_requires=">=3.6",
)