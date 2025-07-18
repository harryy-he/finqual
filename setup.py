from setuptools import setup, find_packages

setup(
    name="finqual",  # This must be unique on PyPI
    version="3.3.0",
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
    python_requires=">=3.6",
    install_requires=["pandas>=2.2.3",
                      "polars>=1.21.0",
                      "cloudscraper>=1.2.71",
                      "requests>=2.32.3"]
)
