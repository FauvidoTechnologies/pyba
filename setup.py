from setuptools import setup, find_packages

from pyba.version import version

setup(
    name="py-browser-automation",
    version=version,
    author="pUrGe12",
    author_email="achintya.jai@owasp.org",
    url="https://github.com/FauvidoTechnologies/PyBrowserAutomation",
    description="Automate online browsing using python and AI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.12.0",
        "google-genai>=1.45.0",
        "openai>=2.6.0",
        "bs4>=0.0.2",
        "playwright>=1.55.0",
        "pyyaml>=6.0.3",
        "python-dotenv>=1.1.1",
        "playwright-stealth>=2.0.0",
        "colorama>=0.4.6",
        "sqlalchemy>=2.0.44",
        "requests>=2.32.5",
        "oxymouse>=1.1.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pyba = pyba.cli.cli_entry:main",
        ],
    },
    python_requires=">=3.10,<4.0",
)
