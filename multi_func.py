from copy import deepcopy
from itertools import combinations


def func_multiplier(funcs:list[any]):
    functions = list(map(lambda func: {'name': func.__name__,
                                  'func': func,
                                  'desc': ' '.join(func.__doc__.split())[
                                      :' '.join(func.__doc__.split()).find('.')
                                  ].replace('Функция, которая возвращает ', ''),
                                  'args': [
                                      arg[:-1].strip() for arg in func.__doc__[
                                      func.__doc__.find(':')+2:
                                  ].split('\n')[:-1]
                                           ]},
                    funcs))
    func_combinations = map(lambda k: combinations(functions, k), range(2, len(funcs)+1))
    final_list = []
    for func_combs in func_combinations:
        for func_comb in func_combs:
            func_comb = list(func_comb)
            func_desc = [func['desc'] for func in func_comb]
            desc = 'Функция, которая возвращает список, содержащий: ' + '; '.join(func_desc) + '.'
            args = '\n        '.join(['']+[arg+'.' for func in func_comb for arg in func['args']]) + '\n    '

            args_and_types = ', '.join(["{0}: {1}".format(key, str(value)[str(value).find(" ")+2: \
                                                                          str(value).find(">")-1]) \
                                        for func in func_comb for key, value in func['func'].__annotations__.items()])
            func_list = []
            for func in func_comb:
                arguments = ', '.join(
                    ["{0}".format(key, str(value)[str(value).find(" ") + 2: str(value).find(">") - 1]) for
                     key, value in func['func'].__annotations__.items()])
                func_list.append(f"{func['name']}({arguments})")
            exec(
f"""def temp_func({args_and_types}):
        func_list = {str(func_list).replace("'", "")[1:-1]}
        return list(func_list)""", globals())
            temp_func.__doc__ = f'\n    {desc}\n\n    Args:' + args
            new_name = '_and_'.join([func['name'] for func in func_comb])
            temp_func.__qualname__ = temp_func.__qualname__.replace(temp_func.__name__, new_name)
            temp_func.__name__ = new_name
            final_list.append(deepcopy(temp_func))
    return final_list+funcs

