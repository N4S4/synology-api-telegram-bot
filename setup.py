from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='synology-api-telegram-bot',
    version='0.1',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='A Telegram bot in Python to interact with your Synology NAS',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['aiogram', 'synology-api'],
    url='https://github.com/N4S4/synology-api-telegram-bot',
    author='Renato Visaggio',
    author_email='synology.python.api@gmail.com'
)