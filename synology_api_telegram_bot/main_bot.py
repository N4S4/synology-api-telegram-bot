import json
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import general_functions as gn
import messages as mex
import syno_functions

# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token='YOUR BOT TOKEN HERE')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

answers = []

#  some global variable for retention during state change

state_string = ''
module_string = None
logged_in = False


# send message after start
@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    gn.check_db_exist()
    await message.answer(mex.start_message(message=True), reply_markup=mex.start_message(keyboard=True))


@dp.message_handler(text='Back to Configuration')
async def return_to_configuration(message: types.Message):
    await message.answer('Here we are back at configuration, \nwhat would you like to change? \n \n'
                         'if nothing you can click on Finish Configuration',
                         reply_markup=mex.start_message(keyboard=True))


@dp.message_handler(text=['modules', 'Back to Modules'])
async def available_modules_keyboard(message: types.Message):
    global logged_in
    if logged_in:
        syno_functions.function_action('logout')
        logged_in = False
    await message.answer('here you go ', reply_markup=mex.show_syno_modules_button())


@dp.message_handler(text=gn.get_syno_modules_name(return_list=True))
async def available_functions_keyboard(message: types.Message):  # it shows the selected module available functions
    global module_string
    message_text = message.text
    module_string = message_text
    await message.answer(f'this are the available function for {message_text} module ',
                         reply_markup=mex.show_module_functions_button(message.text))


@dp.message_handler(text=gn.config_data_list)  # this prepares the states for configuration input from users
async def wait_config_answer(message: types.Message):
    global state_string
    message_text = message.text
    state_string = message_text
    requested_conf = getattr(gn.Form, message_text)  # set the proper state according to message

    await requested_conf.set()
    await message.reply(f'send your {message_text}')


@dp.message_handler(state='*', commands=['cancel'])
async def cancel_handler(message: types.Message, state: FSMContext):
    """Allow user to cancel action via /cancel command"""

    current_state = await state.get_state()
    if current_state is None:
        # User is not in any state, ignoring
        return

    # Cancel state and inform user about it
    await state.finish()
    await message.reply('Cancelled.')


@dp.message_handler(state=gn.Form.ip_address)
@dp.message_handler(state=gn.Form.port)
@dp.message_handler(state=gn.Form.username)
@dp.message_handler(state=gn.Form.password)
@dp.message_handler(state=gn.Form.secure)
@dp.message_handler(state=gn.Form.cert_verify)
@dp.message_handler(state=gn.Form.dsm_version)
@dp.message_handler(state=gn.Form.debug)
@dp.message_handler(state=gn.Form.otp_code)
async def config_answer_write_db(message: types.Message, state: FSMContext):
    gn.write_single_value_to_db(state_string, message.text)
    await state.finish()
    await message.reply(f'Your {state_string} will be  {message.text}, is now stored in config')


@dp.message_handler(text=['Finish Configuration'])
async def finish_configuration(message: types.Message):
    await message.answer('Your configuration is completed, you can change it anytime sending related command. \n '
                         'choose a module from below list ', reply_markup=mex.show_syno_modules_button())


@dp.message_handler(text=['login'])
async def syno_login(message: types.Message):
    global session
    global logged_in
    session = syno_functions.login(module_string)
    logged_in = True
    await message.answer(f'Logging into your synology with your data {session._sid}')


@dp.message_handler(text=gn.get_all_function_lists(return_full_func_list_for_handler=True))
async def function_action(message: types.Message):
    global logged_in
    selected_function = message.text
    logged_in = False
    data = syno_functions.function_action(selected_function, module_string=module_string)
    data = json.dumps(data, indent=4)
    if len(data) >= 4095:  # if message is longer than 4095 characters will split the response in various messages
        num_mess_split = 4095
        list_of_message = [data[i:i+num_mess_split] for i in range(0, len(data), num_mess_split)]
        for string in list_of_message:
            await message.answer(string)
    else:
        await message.answer(f'{data}')


# this is the last line
executor.start_polling(dp)


#  TODO output at logout
