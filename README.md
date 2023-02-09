# Synology API Telegram Bot

The following is a telegram bot using [Synology Api](https://github.com/N4S4/synology-api) library to allow you to 
interact to your NAS via Telegram

## Premises

It requires Python >= 3

It is assumed you know how Telegram and Telegram Bots work, most importantly how to make a new bot with BotFather </br>
there is plenty guides on the web

This bot is <b>NOT</b> a finished product therefore I cannot guarantee it will work all the times or properly.<br>
Use it at your discretion and do not blame or sue me!

It is also considered that if you are here and want to run a bot you know a bit of Python or coding. <br>
Do not open Issues before doing your research (GoogleIt), write me for any concerns.

It still requires work and fine-tuning, like messages and other useless console print.

## Consider My Work

It takes time to work on project like this bla bla bla
Just if you think this code is fun or useful, please cosider to buy me a coffe
- Paypal: https://paypal.me/ren4s4


## Installation

- clone/download this repo <br><br>
- cd synology-api-telegram-bot
- run ```py setup.py install``` or ```python setup.py install``` 
  or ```pip install git+https://github.com/N4S4/synology-api-telegram-bot```

## Usage 

Edit main_bot.py and add your bot TOKEN

```bot = Bot(token='YOUR BOT TOKEN HERE')```

from terminal cd repo folder and run: </br>

```py main_bot.py``` or ```python main_bot.py```

once start polling you will be able to use your bot in 
telegram

## If you do not want to Install

- Download repo
- ```pip install -r requirements.txt```
- cd to repo folder
- run ```py main_bot.py``` or ```python main_bot.py```

## Setting up configuration data

After ```/start``` command, a new file 'conf' is created and will store your data permanently unless you cancel the file,
you will find yourself in front of a keyboard, once all of your Synology data is entered
you can click on ```Finish Configuration``` to proceed to the modules keyboard. <br>

NOTE: if you click on ```Finish Configuration``` prior setting data, it allows you to explore modules and functions, 
but you will not be able to log in.

## Using Modules and Function

You are now on the module keyboard, you can go back to Configuration or click on a module. <br>
Once a module is selected you will be in front of <b>functions</b> keyboard, </br>

Prior to click on any function you will need to log in by clicking ```login``` button,
It is required to log in before any further function action, or it will not reply to the message.

If you want to change module by clicking ```Back o Modules``` the sesssion will log out automatically.

## Issues and TODOs

- Sometimes while setting configuration data might happen that the code adds an extra characters at the end of the 
configuration dictionary, I still have to figure out why but if you get no answer while sending config values consider 
to check your 'conf' file.
- Not sure why doesn't allow me to run it with local net ip_address, some issue with certificate verification 
from request library, still working on it
- You will see some unused functions in genera_functions, is for testing and will be removed later, don't stress yourself with those.
- <b>If the Bot does not respond or seems blocked investigate into your console error output.</br>
- Many other that I still have to discover, fell free to open issues when you find.
