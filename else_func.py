# 주식거래 화면번호 : 0010 ~ 0020
# 수익률조회 화면번호 : 0030 ~ 0050



def change_screen_no(cur_num):      # int로 넘어온다고 가정
    if 1 <= cur_num < 200:
        cur_num += 1
    if cur_num == 200:
        cur_num = 1
    return str(10000 + cur_num)[1:], cur_num

def int_to_byte(input_):
    return str(input_).encode()


def string_to_byte(input_: str):
    return input_.encode()


def list_printer(input_ :list):
    for data in input_:
        print(data)

def spacecontained_string_to_byte(input_ : str):
    return input_.replace(" ", "").encode()

def remove_space(input_: list):
    for datas in input_:
        for data in datas:
            data = data.replace("\t", "").replace(" ", "")
    return input_