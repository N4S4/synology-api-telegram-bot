import inspect
import json
import os

import synology_api as syn
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup  # for reply keyboard

available_mods = {mod for mod in dir(syn) if not mod.startswith('__')}

available_mods_list = list(available_mods)

config_data = {'ip_address', 'port', 'username', 'password', 'secure', 'cert_verify', 'dsm_version', 'debug', 'otp_code'}
config_data_list = list(config_data)


class Form(StatesGroup):
    ip_address = State()
    port = State()
    username = State()
    password = State()
    secure = State()
    cert_verify = State()
    dsm_version = State()
    debug = State()
    otp_code = State()


class RequiredArguments(StatesGroup):
    argument_state = State()


def button_generator():
    button_gen = ReplyKeyboardMarkup(resize_keyboard=True)
    return button_gen


def check_db_exist():
    if os.path.isfile('config'):
        print('Database Exist.')
        return True
    else:
        print('database does not exist creating...')
        config = open('config', 'w')
        initial_data = {}
        for key in config_data:
            initial_data[key] = ''
        json_convert = json.dumps(initial_data)
        json.dump(json_convert, config)
        config.close()


def write_full_conf_to_db(dict):
    f = open('config', 'w')
    json_data = json.dumps(dict)
    json.dump(json_data, f)
    f.close()
    return 'data written to db'


def write_single_value_to_db(key, value):
    f = open('config', 'r+')
    data = get_data_from_db()
    if isinstance(data, str):  # this check if loaded data is dict or string
        data = json.loads(data)
    data[key] = value
    f.seek(0)
    json.dump(data, f, indent=4)
    f.close()
    return 'data written to db ', data


def get_syno_modules_name(return_list=None, return_dict=None):  # returns list or dict with modules name
    modules_name_dict = {mod for mod in dir(syn) if not str(mod).startswith('__') and not str(mod).startswith('error_codes')}
    modules_name_list = list(modules_name_dict)

    if return_list:
        return modules_name_list
    elif return_dict:
        return modules_name_dict


def get_syno_functions(module, return_list=None, return_dict=None, return_func_raw=None):  # returns list or dict with functions name
    if isinstance(module, str):
        module_string = module.replace('/', '')
    else:
        return 'Did you pass a string as module?'
    module = getattr(syn, module_string)
    classes = [cls_name for cls_name, cls_obj in inspect.getmembers(module) if inspect.isclass(cls_obj)]
    func_raw = getattr(module, classes[0])

    class_name_dict = {func for func in dir(func_raw) if not func.startswith('__')}
    class_name_list = list(class_name_dict)

    if return_list:
        return class_name_list
    elif return_dict:
        return class_name_dict
    elif return_func_raw:
        return func_raw


def get_function_arguments(module, function):  # gets all arguments of a function
    classes = get_syno_functions(module, return_func_raw=True)
    arguments_raw = getattr(classes, function)
    arg_string = str(inspect.signature(arguments_raw))
    arg_list = arg_string.replace('(', '')
    arg_list = arg_list.replace(')', '')
    arg_list = arg_list.split(',')

    arguments_list = [var for var in arg_list if var != 'self' and var != 'api_name'
                      and var != 'info' and var != 'api_path' and var != 'req_param']
    return arguments_list


def check_if_require_arguments(module=None, function=None, pass_session_raw=None):  # returns 3 results, a bool, the list of args and message
    if not pass_session_raw:
        list_of_args = [arg for arg in get_function_arguments(module, function)]
    if pass_session_raw:
        list_of_args = [arg for arg in pass_session_raw]
    if not list_of_args:
        return bool(list_of_args), None, f' {function} does not require any arguments \n'
    elif list_of_args:
        return bool(list_of_args), list_of_args, f'{function} requires the following arguments: \n {list_of_args}'


def get_all_function_lists(module_to_return=None, return_list=None, return_dict=None,
                           return_full_func_list_for_handler=None):
    dicti = {}
    module_list = get_syno_modules_name(return_list=True)
    big_list = []
    for a in module_list:
        dicti[a] = []
    for key in dicti:
        dicti[key] = get_syno_functions(module=key, return_list=True)

    for key in dicti:
        for value in dicti[key]:
            big_list.append(value)

    if module_to_return:
        return dicti[module_to_return]
    elif return_dict:
        return dicti
    elif return_list:
        return list(dicti)
    elif return_full_func_list_for_handler:
        return big_list


#  functions = get_all_function_lists(return_dict=True)


def get_data_from_db():
    f = open('config', 'r+')
    data = json.loads(f.read())
    return data


def one_time_first_message():
    message = 'Welcome, this synology_api_telegram_bot uses N4S4/synology-api to allow to interact with your NAS. \n Enjoy using it'
    return
