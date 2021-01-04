import sys
import os
import datetime
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *

import else_func

_FILEPATH = os.path.dirname(__file__)

# 키움증권 API 핸들러


class TextKiwoom(QAxWidget):
    FUNC_LOGIN = "CommConnect()"
    FUNC_SET_INPUT_VALUE = "SetInputValue(QString, QString)"
    FUNC_REQUEST_COMM_DATA = "CommRqData(QString, QString, int, QString)"
    FUNC_GET_LOGIN_INFO = "GetLoginInfo(Qstring)"
    FUNC_GET_COMM_DATA = "GetCommData(QString, QString, int, QString)"
    FUNC_GET_REPEAD_DATA_LEN = "GetRepeatCnt(Qstring, Qstring)"
    FUNC_GET_MARKET_CODELIST = "GetCodeListByMarket(Qstring)"
    FUNC_GET_KOREAN_NAME = "GetMasterCodeName(QString)"
    FUNC_TRADE_JUSIK = "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
    TRAN_SHOWBALANCE = "opw00004"
    TRAN_GETMINDATA = "opt10080"
    TRAN_TRADE_AMOUNT = "OPT10023"

    # 화면번호 관련 (user-setted)
    # 0001 : 계좌잔고 조회
    # 0002 : 거래량급증주식 조회
    # 0003 : 주식거래
    # 0004 : 수익률조회

    def __init__(self):
        super().__init__()

        # set OCX and login Handler
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._login_handler)
        self.OnReceiveTrData.connect(self._receive_tran)
        self.OnReceiveMsg.connect(self._receive_msg)
        self._login()
        
        # set default event handler

        # set receiver
        self._received = False
        self._received_data = []
        # self._received_msg = "" -> 메시지를 보는 방법에 대해, Eventloop과 연계해서 다시 생각해보기

        # set default info
        self._account_num = self._get_account_num()

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
        self._receive_loop = QEventLoop()
        self._receive_loop.exec_()       # _receive_tran이 데이터를 줄 때까지 대기함 (event loop를 비슷하게 구현)
        data = self._received_data
        self._received_data = []
        self._received = False
        return data

    def _receive_msg(self, screen_no, user_define_name, trans_name, server_msg):
        # 이게 대부분 _receive_tran보다 빨리 온다고 가정한다.
        # 문제는, 이게 _receive_tran이 init되지 않은 경우를 가정한다.
        # 즉, data_waiting_loop은 일종의 race condition을 막아주는 역할을 하는 것이다.
        # _receive_tran을 요청하지 않고도 이게 반환될 때는 어떻게 처리해야 하는가?
        # self._received_msg = server_msg
        print(screen_no, user_define_name, trans_name, server_msg)

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
        if user_define_name == "계좌평가현황요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
            # print("Now entered 계좌평가현황요청")
            account_name = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "계좌명")
            balance = self.dynamicCall(self.FUNC_GET_COMM_DATA, trans_name, user_define_name, 0, "예수금")
            # print(account_name, balance)
            self._received_data.append([user_define_name, account_name, balance])
            self._received = True
        if user_define_name == "수익률요청":
            data_length = self.dynamicCall(self.FUNC_GET_REPEAD_DATA_LEN, trans_name, user_define_name)
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
        if user_define_name == "주식거래":
            # print("이게 인식이 되네")
            return
        self._receive_loop.exit()

    def _get_account_num(self):
        account_num = self.dynamicCall(self.FUNC_GET_LOGIN_INFO, ["ACCNO"])
        # print(account_num)
        return str(account_num).replace(";", "")

    def get_highest_trade_amount_jusik(self, minute="15", market="101", request_by_amount="1"):
        """
        거래량 급등 종목들 조회
        :param minute: 30분을 기본으로 함 (이 함수의 호출이 9시 30~40분에 이루어진다 가정)
        :param is_kospi: 코스피 주식을 조회할 것인지 여부 (str))
        :param order_by_percent: 퍼센트로 요청할것인지, 거래량으로 요청할것인지
        :return: 해당 종목들의 코드, 이름, 현재가, 거래 급증량, 거래 급증퍼센트
        """

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시장구분", market)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "정렬구분", request_by_amount)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시간구분", "1")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "거래량구분", "10")  # 만 주 이상만
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "시간", minute)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "종목조건", "1")  # 관리종목 제외하고 불러옴
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "가격구분", "0")

        # print("tran을 서버로 보냅니다.")

        result = self._send_tran("거래량급증요청", self.TRAN_TRADE_AMOUNT, False, "0002")
        result.sort(key=lambda x: x[3])
        result.reverse()
        result = result[:50]
        return result #, self._get_receive_msg()

    def trade_jusik(self, order_type, code, amount, price, is_jijung=False):
        """
        주식을 구매/판매하는 메소드
        :param order_type: 주문의 종류.
            1번이 신규매수, 2번이 신규매도, 3번이 매수최소, 4번이 매도취소, 5번이 매수정정, 6번이 매도정정
        :param code: 거래하고자 하는 주식코드
        :param amount: 거래하고자 하는 주식의 양
        :param price: 거래하고자 하는 주식의 개수
        :param is_jijung: 지정가/시장가 거래할것인지 확인. (True인 경우 지정가로 거래, False인 경우 시장가로 거래)
        :return:
        """

        original_order = ["Error", "", "", "1", "2", "1", "2"]
        jijung = "00" if is_jijung else "03"

        result = self.dynamicCall(self.FUNC_TRADE_JUSIK,            # 주식거래 함수 SendOrder()
                                  ["주식거래",                        # 사용자 구분명
                                   "0003",                          # 화면번호 
                                   self._account_num,               # 계좌번호 10자리
                                   int(order_type),                 # 주문유형
                                   code,                            # 종목코드    
                                   int(amount),                     # 주문수량
                                   price if is_jijung else "",                      # 주문가격
                                   jijung,                          # 거래구분
                                   original_order[int(order_type)]] # 원주문번호
        )
        
        #OnReceiveChejanData 에 체결결과가 나오니 그거 톧로 해볼것
        return result #, self._get_receive_msg()

    def get_balance(self):
        """
        TR opw00004 : 계좌평가현황을 사용
        :param account_num: 예수금을 조회하고자 하는 계좌의 계좌번호
        :return: 계좌의 예수금 (str)
        """

        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "계좌번호", self._account_num)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호", "")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "상장폐지조회구분", "0")  # 상장폐지 조회 구분 포함시 "0", 아닐시 "1"
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호입력매체구분", "00")

        # print("set input value complete, will proceed")

        result = self._send_tran("계좌평가현황요청", self.TRAN_SHOWBALANCE, False, "0001")
        # print(result)
        # print("result :", result)
        # 여기서 에러가 날 경우 (비밀번호 확인 관련) -> 위젯에서 계좌비밀번호 저장 눌러서 저장할 것
        return result[0][2] #, self._get_receive_msg()


    def get_profit(self):
        """
        TR opw00004 : 계좌평가현황을 사용
        :param account_num: 예수금을 조회하고자 하는 계좌의 계좌번호
        :return: 종목당 수익률과 현재가격
        """
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "계좌번호", self._account_num)
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호", "")
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "상장폐지조회구분", "0")  # 상장폐지 조회 구분 포함시 "0", 아닐시 "1"
        self.dynamicCall(self.FUNC_SET_INPUT_VALUE, "비밀번호입력매체구분", "00")

        # print("set input value complete, will proceed")
        result = self._send_tran("수익률요청", self.TRAN_SHOWBALANCE, False, "0004")
        # print(result)
        for i in range(len(result)):
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


# 함수 실험하는 공간
if __name__ == "__main__":
    app = QApplication(sys.argv)
    test = TextKiwoom()
    test.get_profit()
    app.exec_()