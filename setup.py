from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="goldhand",
    version="17.4",
    author="Mihaly",
    author_email="ormraat.pte@gmail.com",
    description="A package working with financial data",
    url="https://github.com/misrori/goldhand",
    license="MIT",
    install_requires=['pandas_datareader', 'pandas==2.2.2', 'pandas_ta==0.4.71b0', 'plotly', 'scipy', 'numpy==1.26.4', 'numba==0.61.2',
                      'numpy', 'requests', 'cloudscraper', 'tqdm'],
    packages=find_packages(),
    # other arguments omitted
    long_description=long_description,
    long_description_content_type='text/markdown'
)

