import else_func
from PyQt5.QAxContainer import QAxWidget


def get_balance_to_byte(func):
    def wrapper(*args):
        value = int(func(*args)[0][0])
        return else_func.int_to_byte(value)

    return wrapper


def get_past_day_data_to_byte(func):
    def wrapper(*args):
        value = func(*args)



def get_past_data_to_byte(func):
    def wrapper(*args):
        value = func(*args)
        # else_func.list_printer(value)
        result = b''
        for datas in value:
            for i in range(0, len(datas) - 1):
                result += else_func.spacecontained_string_to_byte(datas[i])
                result += b','
            result += else_func.spacecontained_string_to_byte(datas[len(datas) - 1])
            result += b'/'
        return result

    return wrapper


def get_highest_trade_amount_jusik_to_byte(func):
    def wrapper(*args):
        value = func(*args)

        # print(value)

        # 리스트 거래량순으로 정렬
        value.sort(key=lambda x: x[3])
        value.reverse()
        value = value[:50]

        # 정렬한 리스트 바이트로 변환
        result = b''
        for i in range(len(value)):
            result += else_func.string_to_byte(value[i][0])
            result += b','
            result += else_func.string_to_byte(value[i][1])
            result += b','
            result += else_func.int_to_byte(value[i][2])
            result += b','
            result += else_func.int_to_byte(value[i][3])
            result += b'/'
        return result

    return wrapper


def trade_jusik_to_byte(func):
    def wrapper(*args):
        value = func(*args)
        return else_func.string_to_byte(value)

    return wrapper


def get_profit_to_byte(func):
    def wrapper(*args):
        value = func(*args)
        else_func.timelog("len(value) : ", len(value), "\tvalue : ", value)

        # byte로 변환하기
        result = b'' + else_func.int_to_byte(len(value)) + b'/'
        for i in range(0, len(value)):
            result += else_func.spacecontained_string_to_byte(value[i][0]) + b','
            result += else_func.spacecontained_string_to_byte(value[i][1]) + b','
            result += else_func.int_to_byte(int(value[i][2])) + b','
            result += else_func.int_to_byte(int(value[i][3])) + b','
            result += else_func.int_to_byte(int(value[i][4])) + b','
            result += else_func.int_to_byte(int(value[i][5])) + b','
            result += else_func.int_to_byte(float(value[i][6])) + b','
            result += else_func.int_to_byte(int(value[i][7])) + b'/'
        return result
    return wrapper


def get_jogunsik_value_to_byte(func):
    def wrapper(*args):
        value = func(*args)

        result = b''
        if not value:
            return result
        result += else_func.string_to_byte(value[0])

        return result

    return wrapper


def program_restart_to_byte(func):
    def wrapper(*args):
        value = func(*args)
        return b'!' + else_func.string_to_byte(value)
    return wrapper


def korean_name_to_byte(func):
    def wrapper(*args):
        value = func(*args)
        result = b''
        result += else_func.string_to_byte(value)
        return result
    return wrapper