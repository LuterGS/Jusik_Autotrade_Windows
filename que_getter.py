import os
import time
import datetime
from multiprocessing import Process
import pika

import kiwoom_main
import else_func

_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"


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
    sleep_time = main_program.receive_data()
    time.sleep(sleep_time)


class QueGetter:
    def __init__(self):
        get_mq_val = GET_MQ_VALUE()
        self._url = get_mq_val["MQ_URL"]
        self._port = get_mq_val["MQ_PORT"]
        self._vhost = get_mq_val["MQ_VHOST"]
        self._cred = pika.PlainCredentials(get_mq_val["MQ_ID"], get_mq_val["MQ_PW"])
        self._send_queue = get_mq_val["MQ_OUT_QUEUE"]
        self._recv_queue = get_mq_val["MQ_IN_QUEUE"]
        self._kiwoom = kiwoom_main.TextKiwoom()

        # 3.6초 시간 조정
        self._time1 = datetime.datetime.now()
        self._time2 = datetime.datetime.now()

        # 종료시간 저장
        self._end_time = 0

    def _timechecker(self):
        # 3.6초 시간 이상이면 통과, 아니면 해당 시간만큼 sleep후 진행
        self._time2 = self._time1
        self._time1 = datetime.datetime.now()
        diff = self._time1 - self._time2
        elapsed_time = diff.seconds + (diff.microseconds/1000000)

        if elapsed_time >= 3.6:
            pass
        else:
            time.sleep(3.6 - elapsed_time)
            self._time1 = datetime.datetime.now()

    def _kiwoom_interact(self, func_value):

        # 3.6초 제한시간 확인
        self._timechecker()

        # input이 여러개일 수 있으니 다듬어줌
        # 여기에도 break 요청이 와야한다고 생각함.
        # 즉, 점검시간에는 일부러 접속을 끊고, 이후에 다시 연결하도록 하는 무언가가 필요함.
        func_value = func_value.split(",")
        # print(func_value)
        if func_value[0] == "잔액요청":
            # print("get acc_num complete, acc_num : ", acc_num)
            result = self._kiwoom.get_balance()
            # print("Successfully processed in _kiwoom_interact", balance)
        elif func_value[0] == "거래량급증요청":
            result = self._kiwoom.get_highest_trade_amount_jusik(func_value[1], func_value[2], func_value[3])
        elif func_value[0] == "주식구매":
            # self, order_type, code, amount, price, is_jijung = False):
            result = self._kiwoom.trade_jusik("1", func_value[1], func_value[2], func_value[3])
        elif func_value[0] == "주식판매":
            result = self._kiwoom.trade_jusik("2", func_value[1], func_value[2], func_value[3])
        elif func_value[0] == "수익률요청":
            result = self._kiwoom.get_profit()
        elif func_value[0] == "프로그램재시작":        # 시간만큼 잠드는 응답 True로 Return
            result = None
            self._end_time = int(func_value[1])
        else:
            print("아직 구현되지 않은 기능입니다 : ", func_value[0])
            return
        # print("Process complete")
        return else_func.result_to_byte(func_value[0], result)

    def receive_data(self):
        conn = pika.BlockingConnection(pika.ConnectionParameters(self._url, int(self._port), self._vhost, self._cred))
        channel = conn.channel()
        while True:
            raw_data = channel.basic_get(queue=self._recv_queue, auto_ack=True) # 3번째꺼가 원하고자 하는 String을 가져와서 처리를 시작한다.
            if raw_data[2] is not None:
                data = raw_data[2].decode().split("|")
                # print("Raw data : ", data)
                # print("middle data : ", data)
                print("요청받은 pid : ", data[0], "  요청받은 항목 : ", data[1])
                data_result = self._kiwoom_interact(data[1])
                result = data[0].encode() + b'|' + data_result
                # print("Final Result : ", result)
                channel.basic_publish(exchange='', routing_key=self._send_queue, body=result)
                # print("요청받은 pid : ", data[0], "  요청받은 항목 : ", data[1], "            완료")
                # channel.basic_get(queue=self._recv_queue, auto_ack=True)  # 작업을 끝마친 후에서야 큐에서 작업을 지운다.
                if self._end_time != 0:
                    return self._end_time



            time.sleep(0.1)

            # 여기에 한시간마다


if __name__ == "__main__":
    while True:
        process1 = Process(target=start_program, args=())
        process1.start()
        process1.join()
