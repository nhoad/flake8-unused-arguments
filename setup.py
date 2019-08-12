from setuptools import setup

requires = [
    "flake8 > 3.0.0",
]

setup(
    name="flake8-unused-arguments",
    license="MIT",
    version="0.0.3",
    description="flake8 extension to warn on unused function arguments",
    author="Nathan Hoad",
    author_email="nathan@hoad.io",
    py_modules=["flake8_unused_arguments"],
    url="https://github.com/nhoad/flake8-unused-arguments",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=requires,
    entry_points={
        "flake8.extension": ["U10 = flake8_unused_arguments:Plugin"],
    },
    classifiers=[
        "Framework :: Flake8",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
