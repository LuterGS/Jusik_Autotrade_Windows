import sys
import os
import datetime
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *

import que_getter

_FILEPATH = os.path.dirname(__file__)

class TextKiwoom(QAxWidget):
    FUNC_LOGIN = "CommConnect()"
    FUNC_SET_INPUT_VALUE = "SetInputValue(QString, QString)"
    FUNC_REQUEST_COMM_DATA = "CommRqData(QString, QString, int, QString)"
    FUNC_GET_LOGIN_INFO = "GetLoginInfo(Qstring)"
    FUNC_GET_COMM_DATA = "GetCommData(QString, QString, int, QString)"
    FUNC_GET_REPEAD_DATA_LEN = "GetRepeatCnt(Qstring, Qstring)"
    FUNC_GET_MARKET_CODELIST = "GetCodeListByMarket(Qstring)"
    FUNC_GET_KOREAN_NAME = "GetMasterCodeName(QString)"
    TRAN_SHOWBALANCE = "opw00004"
    TRAN_GETMINDATA = "opt10080"

    def __init__(self):
        super().__init__()

        # set OCX and login Handler
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._login_handler)
        self.OnReceiveTrData.connect(self._receive_tran)
        self._login()

        # set receiver
        self._received = False
        self._received_data = []


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

    def _send_tran(self, user_define_name, trans_name, is_continue=False, screen_no="0001"):
        """
        명세의 commRqData와, 그 요청한 데이터를 받는 함수
        :param user_define_name: 사용자가 지정한 요청의 이름
        :param trans_name: 실제 호출할 TR 명세
        :param is_continue: 연속 호출인지, 단일 호출인지 (0일시는 단일 조회, 2일시 연속 조회)
        :param screen_no: 화면번호 (최대 200개까지, 0000~0999사이에 생성 가능)
        :return: commRqData로 요청한 TR의 값
        """
        continue_val = 0 if not is_continue else 2
        # print(user_define_name, trans_name, continue_val, screen_no)
        self.dynamicCall(self.FUNC_REQUEST_COMM_DATA, user_define_name, trans_name, continue_val, screen_no)
        # print("Request complete, now proceed")
        self.data_waiting = QEventLoop()
        self.data_waiting.exec_()
        while True:
            if self._received:
                # print(self._received_data)
                data = self._received_data
                self._received_data = []
                self._received = False
                return data

    def _receive_tran(self, screen_no, user_define_name, trans_name, record_name, is_contiune, u1, u2, u3, u4):
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
        # print(user_define_name, trans_name)
        if user_define_name == "계좌평가현황요청":
            # print("Now entered 계좌평가현황요청")
            account_name = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "계좌명")
            balance = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "예수금")
            # print(account_name, balance)
            self._received_data.append([user_define_name, account_name, balance])
            self._received = True
        if user_define_name == "주식분봉차트조회요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            for i in range(data_length):
                timestamp = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "체결시간")
                price = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "현재가")
                amount = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, i, "거래량")
                self._received_data.append([timestamp, price, amount])
            self._received = True
        self.data_waiting.exit()

    def get_account_num(self):
        account_num = self.dynamicCall(self.FUNC_GET_LOGIN_INFO, ["ACCNO"])
        # print(account_num)
        return str(account_num).replace(";", "")

    def get_balance(self, account_num):
        """
        TR opw00004 : 계좌평가현황을 사용
        :param account_num: 예수금을 조회하고자 하는 계좌의 계좌번호
        :return: 계좌의 예수금 (int)
        """

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "계좌번호", account_num)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호", "")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "상장폐지조회구분", "0")    # 상장폐지 조회 구분 포함시 "0", 아닐시 "1"
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호입력매체구분", "00")

        # print("set input value complete, will proceed")

        result = self._send_tran("계좌평가현황요청", self.TRAN_SHOWBALANCE, False, "0001")[0]
        # print("result :", result)
        # 여기서 에러가 날 경우 (비밀번호 확인 관련) -> 위젯에서 계좌비밀번호 저장 눌러서 저장할 것
        return int(result[2])

    def get_kospi_data(self):
        """
        코스피 주식들을 가져와 종목코드_종목이름.txt로 저장
        :return: 성공시 True
        """

    def get_min_jusik_data(self, ticker: str, save_folder=_FILEPATH + "\\data\\"):
        """
        주식 분봉 데이터를 1년치 가져오는 함수. (Request당 900번, 하나당 1분이니 총 112번 요청)
        :param ticker: 주식 종목코드
        :param save_folder: 주식 데이터 저장 폴더
        :return: 성공, 실패값 (bool)
        """
        korean_name = self.dynamicCall(self.FUNC_GET_KOREAN_NAME, ticker)
        # print(ticker + "_" + korean_name + ".txt 진행 중", end="")
        save_file = open(save_folder + ticker + "_" + korean_name + ".txt", "w", encoding="utf8")
        save_file.write("거래시간, 거래가격, 거래량\n")

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE)
