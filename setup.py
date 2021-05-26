from distutils.core import setup

setup(
    name="cloudapi",
    packages=["cloudapi"],
    version="1.0.0",
    license="MIT",
    description="BaseRESTAPI ticker, automaticaly manages request response rate limits and timeouts",
    author="zoran ilievski",
    author_email="pythonic@clientuser.net",
    url="https://github.com/zorani/cloudapi",
    download_url="https://github.com/zorani/cloudapi/archive/refs/tags/v1.0.0.tar.gz",
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
