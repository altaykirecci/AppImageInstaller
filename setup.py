from setuptools import setup, find_packages

setup(
    name="appimage-installer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "setuptools",
    ],
    entry_points={
        'console_scripts': [
            'appimage-installer=appimage:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for installing and managing AppImage applications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/appimage-installer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    include_package_data=True,
    package_data={
        "appimage_installer": ["locales/*.json"],
    },
) 