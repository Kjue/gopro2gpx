import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gopro2json-kjue", # Replace with your own username
    version="0.2.2",
    author="Mikael Lavi",
    author_email="mikael@wanderfeel.com",
    description="Python script that parses the gpmd stream for GOPRO data track embedded in MP4-files and extract the interesting data into a JSON document.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kjue/gopro2json",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)
