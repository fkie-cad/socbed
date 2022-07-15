from setuptools import setup, find_packages

setup(
    name="userbehavior",
    version="1.0.3",
    packages=find_packages(exclude=["*tests"]),
    package_data={"userbehavior.browsing": ["firefox_extensions/*.xpi"]},
    install_requires=["selenium>=3.0.0"],
    entry_points={
        'console_scripts': [
            'userbehavior = userbehavior.run:main',
        ]
    }
)
