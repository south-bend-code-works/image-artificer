from setuptools import setup, find_packages

setup(
    name='ImageArtificer',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'Pillow',
        'matplotlib',
        'colorthief',
        'icrawler',
        'google-cloud-storage',
        'pillow-heif'
    ],
    author='Chris Frederick',
    author_email='chris@sbcodeworks.com',
    description='A package for creating and manipulating images',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/south-bend-code-works/ImageArtificer',  # Replace with your repo URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Or the license you choose
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Adjust based on your compatibility needs
)
