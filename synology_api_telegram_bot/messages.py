from aiogram.types import KeyboardButton  # for reply keyboard

import general_functions as gn


def start_message(message=None, keyboard=None):  # the first message at start command
    if keyboard:
        keyboard_buttons = {'Finish Configuration': KeyboardButton('Finish Configuration')}

        for i in gn.config_data_list:  # conf_buttons:
            keyboard_buttons[str(i)] = KeyboardButton(str(i))

        gen = gn.button_generator()

        for item in keyboard_buttons:
            gen.add(keyboard_buttons[item])
        return gen

    if message:
        return 'Hello, this is a Python Telegram synology_api_telegram_bot that is using ' \
               'https://github.com/N4S4/synology-api to allow you to interact ' \
               'to your Synology NAS via Telegram. \n' \
               'Let\'s start with setting up your configuration \n' \
               'Make sure you setup all variables before proceeding to modules. \n' \
               'your configuration is stored in the same folder as the bot in \'config\' file'


def show_syno_modules_button():  # shows the keyboard with all synology-api modules in the keyboard
    available_mod_keyboard = {'Back to Configuration': KeyboardButton('Back to Configuration')}

    for mod in gn.get_syno_modules_name(return_list=True):
        available_mod_keyboard[str(mod)] = KeyboardButton(str(mod))

    gen = gn.button_generator()

    for b in available_mod_keyboard:
        gen.add(available_mod_keyboard[b])
    return gen


def show_module_functions_button(message):  # show all available functions in the keyboard
    available_func_list = gn.get_syno_functions(message, return_list=True)
    avail_func_keyboard = {'login': KeyboardButton('login'), 'logout': KeyboardButton('logout'),
                           'Back to Modules': KeyboardButton('Back to Modules')}

    for func in available_func_list:
        if func != 'logout':
            avail_func_keyboard[str(func)] = KeyboardButton(func)

    gen = gn.button_generator()

    for key in avail_func_keyboard:
        gen.add(avail_func_keyboard[key])
    return gen
