import synology_api as syn
import general_functions as gn
import inspect

session = None


def login(module_string):
    global session
    module = getattr(syn, module_string)
    classes_text = [cls_name for cls_name, cls_obj in inspect.getmembers(module) if inspect.isclass(cls_obj)]

    classes = getattr(module, classes_text[0])

    config = gn.get_data_from_db()
    print(config)
    print(module_string)
    print(config['cert_verify'])

    session = classes(config['ip_address'], int(config['port']), config['username'], config['password'], bool(config['secure']),
                      bool(config['cert_verify']), int(config['dsm_version']), bool(config['debug']), config['otp_code'])

    return session


def function_action(function, dict_of_args=None, module_string=None): #TODO riuscito a trovare gli argomenti delle funzioni, bisogna passarli se richiesti
    check_bool, check_list, check_message = gn.check_if_require_arguments(module_string, function)
    data = getattr(session, function)
    if check_bool:
        if not dict_of_args:
            return bool(check_bool), check_list, check_message
    elif not check_bool:
        print(data())
        return data()
