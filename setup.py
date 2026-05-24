from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="synology-api-telegram-bot",
    version="0.2.0",
    author="N4S4",
    description="Telegram bot to control Synology NAS via synology-api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/N4S4/synology-api-telegram-bot",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "aiogram>=3.0,<4.0",
        "synology-api>=0.8.0",
        "python-dotenv>=1.0,<2.0",
    ],
    entry_points={
        "console_scripts": [
            "synology-bot=synology_api_telegram_bot.main_bot:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
