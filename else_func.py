# 주식거래 화면번호 : 0010 ~ 0020
# 수익률조회 화면번호 : 0030 ~ 0050
def change_screen_no(cur_num):      # int로 넘어온다고 가정
    if 1 <= cur_num < 200:
        cur_num += 1
    if cur_num == 200:
        cur_num = 1
    return str(10000 + cur_num)[1:], cur_num


def raw_result_to_result(result_name, result):
    if result == []:
        print("\b  IS FAILED")
        return ""

    if result_name == "거래량급증요청":
        result.sort(key=lambda x: x[3])
        result.reverse()
        result = result[:50]
        return result
    elif result_name == "계좌평가현황요청":
        return result[0][2]
    elif result_name == "수익률요청":
        # print("whole : ", result)
        #end_val = 1 if result[0] == 0 else result[0] + 1
        result[0] = str(result[0])
        # print(end_val)
        for i in range(1, len(result)):
            # print("test : ", result[i])
            result[i][0] = result[i][0].replace(" ", "")[1:]        # 종목코드
            result[i][1] = result[i][1].replace(" ", "")            # 종목이름
            result[i][2] = str(int(result[i][2]))                        # 보유량
            result[i][3] = str(int(result[i][3]))                        # 매입금액
            result[i][4] = str(int(result[i][4]))                        # 평가금액
            result[i][5] = str(int(result[i][5]))                        # 손익금액
            result[i][6] = str(float(result[i][6]))                      # 수익률
            result[i][7] = str(int(result[i][7]))                   # 현재가
        # print(result)
        return result





def result_to_byte(result_name, kiwoom_result):
    if kiwoom_result == "":
        return b'FAIL'

    if result_name == "잔액요청":
        return string_to_byte(kiwoom_result)
    elif result_name == "주식분봉차트조회요청":
        result = b''
        for datas in kiwoom_result:
            for i in range(0, len(datas)-1):
                result += string_to_byte(datas[i])
                result += b','
            result += string_to_byte(datas[len(datas) - 1])
            result += b'/'
        return result

    elif result_name == "거래량급증요청":
        # 여기에 진입한다는 소리는, 무조건 list는 50개, 각 원소는 4개의 요소를 가진 list라는 소리다.
        # 즉, 무조건 for문에서 상수로 선언해서 접근한다.
        result = b''
        for i in range(len(kiwoom_result)):
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
        result = b''
        result += string_to_byte(kiwoom_result[0]) + b'/'
        for i in range(1, len(kiwoom_result)):
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


def list_printer(input_ :list):
    for data in input_:
        print(data)

def remove_space(input_: list):
    for datas in input_:
        for data in datas:
            data = data.replace("\t", "").replace(" ", "")
    return input_