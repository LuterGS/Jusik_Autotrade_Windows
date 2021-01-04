
def result_to_byte(result_name, kiwoom_result):
    if result_name == "잔액요청":
        return string_to_byte(kiwoom_result)
    elif result_name == "거래량급증요청":
        # 여기에 진입한다는 소리는, 무조건 list는 50개, 각 원소는 4개의 요소를 가진 list라는 소리다.
        # 즉, 무조건 for문에서 상수로 선언해서 접근한다.
        result = b''
        for i in range(50):
            result += string_to_byte(kiwoom_result[i][0])
            result += b','
            result += string_to_byte(kiwoom_result[i][1])
            result += b','
            result += int_to_byte(kiwoom_result[i][2])
            result += b','
            result += int_to_byte(kiwoom_result[i][3])
            result += b'/'
        return result
    elif result_name == "주식구매" or result_name == "주식판매":
        return int_to_byte(kiwoom_result)
    elif result_name == "수익률요청":
        # print(kiwoom_result)
        result = b''

        for i in range(len(kiwoom_result)):
            for j in range(7):
                result += string_to_byte(kiwoom_result[i][j])
                result += b','
            result += string_to_byte(kiwoom_result[i][7])
            result += b'/'

        return result
    elif result_name == "프로그램재시작":
        return b'RESTART'



def int_to_byte(input_):
    return str(input_).encode()


def string_to_byte(input_: str):
    return input_.encode()