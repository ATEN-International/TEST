import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ai-voice-sdk",
    version="0.0.1",
    author="yimin",
    author_email="no@example.com",
    description="This is aten ai voice sdk",
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
        # 'python-magic-bin==0.4.14',
    ],
)