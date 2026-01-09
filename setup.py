from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="goldhand",
    version="20.4",
    author="Mihaly",
    author_email="ormraat.pte@gmail.com",
    description="A package working with financial data",
    url="https://github.com/misrori/goldhand",
    license="MIT",
    install_requires=['pandas', 'plotly', 'scipy', 'numpy', 'numba',
                      'requests', 'tqdm', 'yfinance<1.0', 'ipython'],
    packages=find_packages(),
    # other arguments omitted
    long_description=long_description,
    long_description_content_type='text/markdown'
)

