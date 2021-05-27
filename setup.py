from distutils.core import setup

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.html"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cloudapi",
    packages=["cloudapi"],
    version="1.0.6",
    license="MIT",
    description="BaseRESTAPI ticker, automaticaly manages request response rate limits and timeouts",
    long_description=long_description,
    long_description_content_type="text/html",
    author="zoran ilievski",
    author_email="pythonic@clientuser.net",
    url="https://github.com/zorani/cloudapi",
    download_url="https://github.com/zorani/cloudapi/archive/refs/tags/v1.0.6.tar.gz",
    keywords=["baseapi", "requests", "rate limit", "rate limits", "api"],
    install_requires=["requests"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
