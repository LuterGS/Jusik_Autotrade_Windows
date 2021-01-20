import sys
import os
import datetime
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *

import else_func
import kiwoom_parser

_FILEPATH = os.path.dirname(__file__)

# 키움증권 API 핸들러


class TextKiwoom(QAxWidget):
    FUNC_LOGIN = "CommConnect()"
    FUNC_SET_INPUT_VALUE = "SetInputValue(QString, QString)"
    FUNC_REQUEST_COMM_DATA = "CommRqData(QString, QString, int, QString)"
    FUNC_GET_LOGIN_INFO = "GetLoginInfo(QString)"
    FUNC_GET_COMM_DATA = "GetCommData(QString, QString, int, QString)"
    FUNC_GET_REPEAD_DATA_LEN = "GetRepeatCnt(Qstring, Qstring)"
    FUNC_GET_MARKET_CODELIST = "GetCodeListByMarket(Qstring)"
    FUNC_GET_KOREAN_NAME = "GetMasterCodeName(QString)"
    FUNC_TRADE_JUSIK = "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
    FUNC_REQUEST_JOGUNSIK_LIST = "GetConditionLoad()"
    FUNC_REQUEST_JOGUNSIK = "SendCondition(QString, QString, int, int)"
    FUNC_GET_JOGUNSIK_STRING = "GetConditionNameList()"
    TRAN_SHOWBALANCE = "opw00004"
    TRAN_GETMINDATA = "opt10080"
    TRAN_TRADE_AMOUNT = "OPT10023"

    # 화면번호 관련
    # 하나로 고정하면 안된다고 한다. 그러니, 함수를 호출해서 1~200 사이의 값을 순회하도록 하자.
    # 이유 : 특정 요청에 대해 하나로 화면번호를 고정하면 오류가 날 수 있음

    def __init__(self):
        super().__init__()

        # set OCX and login Handler
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._login_handler)
        self.OnReceiveTrData.connect(self._receive_tran)
        self.OnReceiveMsg.connect(self._receive_msg)
        self.OnReceiveRealData.connect(self._receive_realdata)
        # self.OnReceiveChejanData.connect(self._receive_chejan)
        self.OnReceiveConditionVer.connect(self._receive_condition)
        self.OnReceiveTrCondition.connect(self._receive_jogunsikdata)
        self._login()

        # set receiver
        self._received = False
        self._received_data = []
        # self._received_msg = "" -> 메시지를 보는 방법에 대해, Eventloop과 연계해서 다시 생각해보기

        # set timeout timer
        # for send_tran
        self._timer = QTimer()
        self._timer.setInterval(10000)
        self._timer.timeout.connect(self._loop_end)

        # for trade_jusik
        self._trade_timer = QTimer()
        self._trade_timer.setInterval(10000)
        self._trade_timer.timeout.connect(self._trade_loop_end)

        # for get_jogunsik_list
        # self._jogunsik_list_timer = QTimer()
        # self._jogunsik_list_timer.setInterval(10000)
        # self._jogunsik_list_timer.timeout.connect(self._jogunsik_list_loop_end)

        # for get_jogunsik_value
        self._jogunsik_value_timer = QTimer()
        self._jogunsik_value_timer.setInterval(10000)
        self._jogunsik_value_timer.timeout.connect(self._jogunsik_value_loop_end)

        # set default info
        self._account_num = self._get_account_num()

        # 화면번호 리스트
        self._screen_no = 1

        # 조건식 인덱스
        self._jogunsik_index = 0

    def _login(self):
        self.dynamicCall(self.FUNC_LOGIN)
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _login_handler(self, message):
        if message == 0:
            print(str(datetime.datetime.now()) + "  키움증권 서버 로그인 성공")
        else:
            print(str(datetime.datetime.now()) + "  키움증권 서버 로그인 실패, err:", message)
            # 여기에 재로그인 시도 코드를 작성할 수 있지만, 일단 생략
            exit(1)
        self.login_event_loop.exit()

    def _send_tran(self, user_define_name, trans_name, is_continue=False):
        """
        명세의 commRqData와, 그 요청한 데이터를 받는 함수
        :param user_define_name: 사용자가 지정한 요청의 이름
        :param trans_name: 실제 호출할 TR 명세
        :param is_continue: 연속 호출인지, 단일 호출인지 (0일시는 단일 조회, 2일시 연속 조회)
        :param screen_no: 화면번호 (최대 200개까지, 0000~0999사이에 생성 가능)
        :return: commRqData로 요청한 TR의 값
        """
        # 계속 값이 들어올 것인지를 조정
        continue_val = 0 if not is_continue else 2
        
        # 화면번호 변경
        screen_no, self._screen_no = else_func.change_screen_no(self._screen_no)
        # print("화면번호 변경 완료")
        
        # 함수 호출
        self.dynamicCall(self.FUNC_REQUEST_COMM_DATA, user_define_name, trans_name, continue_val, screen_no)
        # print("Request complete, now proceed")
        
        # 이벤트루프 설정 (signal wait과 비슷) 및 Timeout 설정
        self._receive_loop = QEventLoop()
        self._timer.start()

        # print("Reached Here!")
        
        # 이벤트루프 실행
        self._receive_loop.exec_()       # _receive_tran이 데이터를 줄 때까지 대기함 (event loop를 비슷하게 구현)
        
        # 정상적으로 이벤트루프가 break되었을 때 Timer를 중지함
        self._timer.stop()
        
        # 이벤트루프가 깨진 이후 데이터를 받아옴
        # 정상적으로 값을 받아왔을 때는 값이 들어있고, 아니면 값이 들어있지 않음
        data = self._received_data
        # print(data)
        self._received_data = []
        self._received = False

        return data

    def _loop_end(self):
        self._receive_loop.exit()
        self._timer.stop()
        print("timer is called!")
        
    def _trade_loop_end(self):
        self._trade_jusik_loop.exit()
        self._trade_timer.stop()
        print("trade timer is called!")

    def _jogunsik_value_loop_end(self):
        self._jogunsik_value_loop.exit()
        self._jogunsik_value_timer.stop()
        print("jogunsik value timer is called!")



    def _receive_condition(self, num1, num2):
        print("Received Condition : ", num1, num2)
        value = str(self.dynamicCall(self.FUNC_GET_JOGUNSIK_STRING)).split(";")
        value.pop()
        for i in range(len(value)):
            value[i] = value[i].split("^")
            value[i][0] = int(value[i][0])

        # else_func.timelog("value : ", value)

        screen_no, self._screen_no = else_func.change_screen_no(self._screen_no)
        self.dynamicCall(self.FUNC_REQUEST_JOGUNSIK, screen_no, value[self._jogunsik_index][1], value[self._jogunsik_index][0], 0)


    def _receive_realdata(self, code, type, data):
        # OnReceiveRealData() 의 Python 구현형
        print(code, type, data)

    def _receive_chejan(self, gubun, item_len, data_list):
        # OnReceiveChejanData() 의 Python 구현형
        # print(gubun, item_len, data_list)
        pass

    def _receive_jogunsikdata(self, screen_no, code_list, jogunsik_name, index, cont):
        # else_func.timelog("Entered 2nd callback")
        # else_func.timelog(screen_no, code_list, jogunsik_name, index, cont)
        self._received_data.append(str(code_list)[:-1].replace(";", ","))
        self._received = True
        self._jogunsik_value_loop.exit()

    def _receive_msg(self, screen_no, user_define_name, trans_name, server_msg):
        # 이게 대부분 _receive_tran보다 빨리 온다고 가정한다.
        # 문제는, 이게 _receive_tran이 init되지 않은 경우를 가정한다.
        # 즉, data_waiting_loop은 일종의 race condition을 막아주는 역할을 하는 것이다.
        # _receive_tran을 요청하지 않고도 이게 반환될 때는 어떻게 처리해야 하는가?
        # self._received_msg = server_msg
        print("server msg : " + screen_no + "|" + user_define_name + "|" + trans_name + "|" + server_msg)
        if user_define_name == "주식거래":      # 여기서 에러처리도 가능함
            self._trade_jusik_loop.exit()
            # print("reachd htere!")

    def _receive_tran(self, screen_no, user_define_name, trans_name, record_name, is_continue, u1, u2, u3, u4):
        """
        실제 Transaction의 이벤트 핸들러인 OnReceiveTrData의 Python 변형 형이다
        :param screen_no: _send_tran에서 사용자가 지정해준 화면 번호이다
        :param user_define_name: _send_tran에서 지정해준 사용자가 지정한 요청의 이름이다
        :param trans_name: _send_tran에서 호출한 실제 TR 이름이다.
        :param record_name: 추측 중
        :param is_contiune: 연속인지, 단일 호출인지를 판별한다. (0일시 단일, 2일시 연속)
        :param u1 ~ u4: 불필요한 값 (명세에 그렇게 정의되어있음)
        :return: 없음. self.received_data에 값을 넣어주는게 끝
        """
        # print(user_define_name, trans_name, is_continue)
        if user_define_name == "예수금상세현황요청":
            v1 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "예수금")
            # print("p")
            v2 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "주식증거금현금")
            # print("p")
            v3 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "수익증권증거금현금")
            # print("p")
            v4 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "신용보증금현금")
            # print("p")
            v5 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "기타증거금")
            # print("p")
            v6 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "미수확보금")
            # print("p")
            v7 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "주문가능금액")

            # balance = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "예수금")
            # print(account_name, balance)
            self._received_data.append([v1, v2, v3, v4, v5, v6, v7])
            self._received = True
        if user_define_name == "수익률요청":
            # print("in complete")
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            self._received_data.append(data_length)
            for i in range(data_length):
                code = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "종목코드")
                name = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "종목명")
                amount = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "보유수량")
                price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "매입금액")
                cur_price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "평가금액")
                profit_price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "손익금액")
                percent = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "손익율")
                sell_price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "현재가")
                self._received_data.append([code, name, amount, price, cur_price, profit_price, percent, sell_price])
            self._received = True
            # print("out complete")
        if user_define_name == "주식분봉차트조회요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            for i in range(data_length):
                timestamp = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "체결시간")
                price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "현재가")
                amount = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "거래량")
                self._received_data.append([timestamp, price, amount])
            self._received = True
        if user_define_name == "거래량급증요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            for i in range(data_length):
                code = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "종목코드")
                name = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "종목명")
                price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "현재가")
                amount = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "급증량")
                # percent = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "급증률")
                result_list = [code.replace(" ", ""), name.replace(" ", ""), abs(int(price.replace(" ", ""))), abs(int(price.replace(" ", ""))) * abs(int(amount.replace(" ", "")))]
                self._received_data.append(result_list)
            self._received = True
        if user_define_name == "주식분봉차트조회요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            print("len : ", data_length)
            for i in range(data_length):
                v1 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "체결시간")
                v2 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "현재가")
                v3 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "거래량")
                v4 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "시가")
                v5 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "고가")
                v6 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "저가")
                v7 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "수정주가구분").strip()
                v8 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "수정비율").strip()
                v9 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "대업종구분").strip()
                v10 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "소업종구분").strip()
                v11 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "종목정보").strip()
                v12 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "수정주가이벤트").strip()
                v13 = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "전일종가").strip()
                # print([v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13])
                self._received_data.append([v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13])
            self._received = True
        if user_define_name == "주식거래":
            print("주식거래 : ", user_define_name, trans_name, record_name)
            return
        self._receive_loop.exit()

    def _get_account_num(self):
        account_num = self.dynamicCall(self.FUNC_GET_LOGIN_INFO, ["ACCNO"])
        print(account_num)
        return str(account_num).replace(";", "")

    @kiwoom_parser.get_highest_trade_amount_jusik_to_byte
    def get_highest_trade_amount_jusik(self, args): #minute="15", market="101", request_by_amount="1", is_min="1"):
        """
        거래량 급등 종목들 조회
        !! args가 0은 함수번호, 이후 1, 2, 3, 4가 아래와 같은 형식으로 들어와야 함! !!
        :param minute: 조회분
        :param market: 시장 (코스피, 코스닥, 전체)
        :param request_by_amount: 거래량혹은 거래액으로 조회
        :param is_min: 분으로 조회할건지, 전날거래량 기준으로 조회할건지
        :return: 해당 종목들의 코드, 이름, 현재가, 거래 급증량, 거래 급증퍼센트
        """
        minute = args[1]
        market = args[2]
        request_by_amount = args[3]
        is_min = args[4]

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시장구분", market)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "정렬구분", request_by_amount)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시간구분", is_min)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "거래량구분", "10")  # 만 주 이상만
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시간", minute)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "종목조건", "1")  # 관리종목 제외하고 불러옴
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "가격구분", "0")

        # print("tran을 서버로 보냅니다.")

        result = self._send_tran("거래량급증요청", self.TRAN_TRADE_AMOUNT, False)
        return result

    @kiwoom_parser.trade_jusik_to_byte
    def trade_jusik(self, args): #order_type, code, amount, price, is_jijung=False):
        """
        주식을 구매/판매하는 메소드
        !! args가 0은 함수번호, 이후 1, 2, 3, 4, 5가 각각에 맞게 들어와야 함 !!
        :param order_type: 주문의 종류.
            1번이 신규매수, 2번이 신규매도, 3번이 매수최소, 4번이 매도취소, 5번이 매수정정, 6번이 매도정정
        :param code: 거래하고자 하는 주식코드
        :param amount: 거래하고자 하는 주식의 양
        :param price: 거래하고자 하는 주식의 개수
        :param is_jijung: 지정가/시장가 거래할것인지 확인. (True인 경우 지정가로 거래, False인 경우 시장가로 거래)
        :return:
        """
        order_type = args[1]
        code = args[2]
        amount = args[3]
        price = args[4]
        jijung = args[5]

        original_order = ["Error", "", "", "1", "2", "1", "2"]
        screen_no, self._screen_no = else_func.change_screen_no(self._screen_no)

        result = self.dynamicCall(self.FUNC_TRADE_JUSIK,            # 주식거래 함수 SendOrder()
                                  ["주식거래",                        # 사용자 구분명
                                   screen_no,                          # 화면번호
                                   self._account_num,               # 계좌번호 10자리
                                   int(order_type),                 # 주문유형
                                   code,                            # 종목코드    
                                   int(amount),                     # 주문수량
                                   price if jijung == "00" else "",                      # 주문가격
                                   jijung,                          # 거래구분
                                   original_order[int(order_type)]] # 원주문번호
        )
        
        # 이벤트 핸들러 설정 (sigwait과 비슷)
        # timeout을 10초로 설정함.
        self._trade_jusik_loop = QEventLoop()
        self._trade_timer.start()
        self._trade_jusik_loop.exec_()
        self._trade_timer.stop()
        print("Now reached here, result : ", result)

        # TODO : 결과값을 OnReceiveMsg에 따라 다르게 하는 방법 강구해볼것

        return "1"

    @kiwoom_parser.get_balance_to_byte
    def get_balance(self, args):
        """
        TR opw00004 : 계좌평가현황을 사용
        :param account_num: 예수금을 조회하고자 하는 계좌의 계좌번호
        :return: 계좌의 예수금 (str)
        """

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "계좌번호", self._account_num)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호", "")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호입력매체구분", "00")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "조회구분", "2")

        # print("set input value complete, will proceed")

        result = self._send_tran("예수금상세현황요청", self.TRAN_SHOWBALANCE, False)
        # print("final result is : ", result)
        # print("result :", result)
        # 여기서 에러가 날 경우 (비밀번호 확인 관련) -> 위젯에서 계좌비밀번호 저장 눌러서 저장할 것
        return result

    @kiwoom_parser.get_profit_to_byte
    def get_profit(self, args):
        """
        TR opw00004 : 계좌평가현황을 사용
        :param account_num: 예수금을 조회하고자 하는 계좌의 계좌번호
        :return: 종목당 수익률과 현재가격
        """
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "계좌번호", self._account_num)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호", "")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "상장폐지조회구분", "0")  # 상장폐지 조회 구분 포함시 "0", 아닐시 "1"
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호입력매체구분", "00")

        result = self._send_tran("수익률요청", self.TRAN_SHOWBALANCE, False)
        return result
        # print(result)


    def get_highest_jusik_data(self, num=200):
        pass

    @kiwoom_parser.get_min_past_data_to_byte
    def get_min_past_data(self, args: list):#code, is_continue="0"):
        """
        요청한 주식 정보를 되돌려주는 함수
        !! args가 함수번호, code, is_continue순으로 들어와야 함 !!
        :param code: 종목코드 (6자리 str)
        :param is_continue: 반복인지 (처음 요청시 0, 반복시 2)
        :return: 해당 주식 종목값
        """
        code = args[1]
        is_continue = args[2]
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "종목코드", code)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "틱범위", "1")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "수정주가구분", "0")
        cont = False if is_continue == "0" else True

        result = self._send_tran("주식분봉차트조회요청", self.TRAN_GETMINDATA, cont)
        return result

    @kiwoom_parser.program_restart_to_byte
    def program_restart(self, args: list):
        """
        !! args는 0이 함수번호, 1이 sleep 시간이다.
        :param args:
        :return:
        """

        return args[1]

    @kiwoom_parser.get_jogunsik_value_to_byte
    def get_jogunsik_value(self, args: list): #jogunsik_index: int):
        """
        !! args는 0이 함수번호, 1이 index여야 함! (str)
        :param args:
        :return:
        """

        self._jogunsik_index = int(args[1])

        result = self.dynamicCall(self.FUNC_REQUEST_JOGUNSIK_LIST)

        self._jogunsik_value_loop = QEventLoop()
        self._jogunsik_value_timer.start()
        self._jogunsik_value_loop.exec_()
        self._jogunsik_value_timer.stop()

        data = self._received_data
        self._received_data = []
        self._received = False

        return data




# 함수 실험하는 공간
if __name__ == "__main__":
    app = QApplication(sys.argv)
    test = TextKiwoom()
    val = test.get_jogunsik_value([0, "0"])
    print("result : ", val)

    # app.exec_()