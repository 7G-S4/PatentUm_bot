# -*- coding: utf-8 -*-

def get_n_ip_info(n: int):
    """
    Функция, которая возвращает информацию о патенте(изобретении) под номером n, заданным пользователем.

    Args:
        n: Порядковый номер патента(изобретения).
    """
    return f"Патент номер {n} о телефоне на гидромоторе, разработан в 1231 году"

#dataset.query({'num': n}, ['summary'])[0][0]

setattr(get_n_ip_info, "name_returnable_value", "n_patent_info")
setattr(get_n_ip_info, "is_answer", False)

def get_sum_a_b(num_list:list[any([int, float])]):
    """
    Функция, которая возвращает сумму всех чисел из списка num_list, заданным пользователем, то есть выполняет операцию сложения：складывает числа.

    Args:
        num_list: Список с целыми и вещественными числами.
    """
    return sum(num_list)

setattr(get_sum_a_b, "is_answer", True)
setattr(get_sum_a_b, "answer", "Сумма равна val")
setattr(get_sum_a_b, "name_returnable_value", "sum_a_b")

class Functions:
    def __init__(self):
        self.get_n_ip_info = get_n_ip_info
        self.get_sum_a_b = get_sum_a_b