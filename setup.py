import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ai-voice-sdk",
    version="0.0.2",
    author="ATEN-International",
    author_email="rdmaten@aten.com.tw",
    url="https://github.com/ATEN-International/ai-voice-sdk-python",
    description="Aten AI Voice SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'requests',
    ],
)