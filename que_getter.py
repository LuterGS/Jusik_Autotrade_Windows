import os
import time
import datetime
from multiprocessing import Process
import pika

import kiwoom_main
import else_func

_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
_WAIT_TIME = 3.6


def GET_MQ_VALUE():
    return_val = {}
    with open(_PATH + "MQ_CRED.txt", "r", encoding='utf8') as mqfile:
        for line in mqfile:
            line = line.replace("\n", "").split("=")
            return_val[line[0]] = line[1]
    return return_val


def start_program():
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    main_program = QueGetter()




class QueGetter:

    get_mq_val = GET_MQ_VALUE()
    _url = get_mq_val["MQ_URL"]
    _port = get_mq_val["MQ_PORT"]
    _vhost = get_mq_val["MQ_VHOST"]
    _cred = pika.PlainCredentials(get_mq_val["MQ_ID"], get_mq_val["MQ_PW"])
    _send_queue = get_mq_val["MQ_OUT_QUEUE"]
    _recv_queue = get_mq_val["MQ_IN_QUEUE"]
    _sleep_save = get_mq_val["MQ_SLEEP_QUEUE"]

    def __init__(self):
        # 키움증권 로딩
        self._kiwoom = kiwoom_main.TextKiwoom()

        self.conn = pika.BlockingConnection(pika.ConnectionParameters(self._url, int(self._port), self._vhost, self._cred))
        channel = self.conn.channel()

        # 기본적으로 돌아가는 consumer, callback 설정
        channel.basic_consume(
            queue=self._recv_queue,
            on_message_callback=lambda ch, deli, prop, val:
                QueGetter.receive_data(self._kiwoom, self._kiwoom_interact, ch, deli, prop, val, self._send_queue),
            auto_ack=True
        )
        channel.start_consuming()


    def _timechecker(self):
        # 3.6초 시간 이상이면 통과, 아니면 해당 시간만큼 sleep후 진행
        self._time2 = self._time1
        self._time1 = datetime.datetime.now()
        diff = self._time1 - self._time2
        elapsed_time = diff.seconds + (diff.microseconds/1000000)

        if elapsed_time >= _WAIT_TIME:
            pass
        else:
            time.sleep(_WAIT_TIME - elapsed_time)
            self._time1 = datetime.datetime.now()

    @staticmethod
    def _kiwoom_interact(kiwoom :kiwoom_main.TextKiwoom, func_value):

        # 프로그램의 구매/판매는 즉각적으로 이루어져야 하므로 linux 서버에서 sleep을 자의적으로 줌
        # self._timechecker()

        # input이 여러개일 수 있으니 다듬어줌
        # 여기에도 break 요청이 와야한다고 생각함.
        # 즉, 점검시간에는 일부러 접속을 끊고, 이후에 다시 연결하도록 하는 무언가가 필요함.
        func_value = func_value.split(",")
        # print(func_value)
        if func_value[0] == "잔액요청":
            # print("get acc_num complete, acc_num : ", acc_num)
            result = kiwoom.get_balance()
            # print("Successfully processed in _kiwoom_interact", balance)
        elif func_value[0] == "주식분봉차트조회요청":
            result = kiwoom.get_min_past_data(func_value[1], func_value[2])
        elif func_value[0] == "거래량급증요청":
            result = kiwoom.get_highest_trade_amount_jusik(func_value[1], func_value[2], func_value[3], func_value[4])
        elif func_value[0] == "주식구매":
            # self, order_type, code, amount, price, is_jijung = False):
            result = kiwoom.trade_jusik("1", func_value[1], func_value[2], func_value[3])
        elif func_value[0] == "주식판매":
            result = kiwoom.trade_jusik("2", func_value[1], func_value[2], func_value[3])
        elif func_value[0] == "수익률요청":
            result = kiwoom.get_profit()
        elif func_value[0] == "프로그램재시작":        # 시간만큼 잠드는 응답 True로 Return
            return b'RESTART', int(func_value[1])
        else:
            print("아직 구현되지 않은 기능입니다 : ", func_value[0])
            return
        # print("Process complete, value is ", result)
        return else_func.result_to_byte(func_value[0], result), 0

    @staticmethod
    def receive_data(kiwoom, kiwoom_func, channel, deliver_info, properties, value :bytes, send_queue):
        value = value.decode().split("|")
        print(str(datetime.datetime.now()), "\t요청받은 pid : ", value[0], "\t요청받은 항목 : ", value[1])
        kiwoom_result, sleep = kiwoom_func(kiwoom, value[1])
        final_result = value[0].encode() + b"|" + kiwoom_result
        channel.basic_publish(exchange='', routing_key=send_queue, body=final_result)

        # 만약 프로그램이 종료되어야 할 때
        if sleep != 0:
            time.sleep(sleep)
            exit(1)


if __name__ == "__main__":
    while True:
        process1 = Process(target=start_program, args=())
        process1.start()
        process1.join()
