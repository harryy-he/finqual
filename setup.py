from setuptools import setup, find_packages

setup(
    name="finqual",  # This must be unique on PyPI
    version="4.5.7",
    author="Harry",
    description="A Python package to help investors to conduct financial research, analysis and comparable company analysis.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/harryy-he/finqual",  # optional, update if you have a repo
    packages=find_packages(),  # Automatically includes finqual/
    include_package_data=True,
    package_data={'finqual': ['data/*.parquet', 'data/*.json', 'node_classes/*.py', 'sec_edgar/*.py']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # or whichever license you use
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10", 
    install_requires=["pandas>=2.2.3",
                      "polars>=1.35.1",
                      "cloudscraper>=1.2.71",
                      "requests==2.32.4",
                      "ratelimit>=2.2.1",
                      "matplotlib>=3.8.0",
                      "pyarrow>=12.0.0",
                      "ijson>=3.4.0",
                      "numpy>=2.2.6",
                      "pydantic==2.12.4"
                      ]
)

# On Pycharm, ONLY commit the "DO NOT COMMIT AND PUSH", then go to "Git Log" then tag the new commit by right clicking
# and adding a new version, then right click on that and click on "Push All Up to Here", then right click on the TAG and
# click "Push to origin".
