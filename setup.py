from distutils.core import setup

with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()

setup(
    name='finqual',
    version='2.0.0',
    description='A package to retrieve historical fundamental financial data such as income statement, balance sheet, and cash flow statement directly from the SEC with no request caps and fast request rate limits.',
    author='Harry',
    url = "https://github.com/Myztika/finqual",
    packages=['finqual'],
    package_dir = {'finqual':"finqual"},
    package_data={'finqual': ['data/*.csv', 'data/*.json']},
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
