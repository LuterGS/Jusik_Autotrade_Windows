import os
import time
import datetime
import pika

import kiwoom_main

_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"


def GET_MQ_VALUE():
    return_val = {}
    with open(_PATH + "MQ_CRED.txt", "r", encoding='utf8') as mqfile:
        for line in mqfile:
            line = line.replace("\n", "").split("=")
            return_val[line[0]] = line[1]
    return return_val


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

    def _kiwoom_interact(self, func_name):
        self._timechecker()

        if func_name == "잔액요청":
            acc_num = self._kiwoom.get_account_num()
            # print("get acc_num complete, acc_num : ", acc_num)
            balance = self._kiwoom.get_balance(acc_num)
            # print("Successfully processed in _kiwoom_interact", balance)
            return str(balance).encode()
        else:
            print(func_name)

    def receive_data(self):
        conn = pika.BlockingConnection(pika.ConnectionParameters(self._url, int(self._port), self._vhost, self._cred))
        channel = conn.channel()
        while True:
            raw_data = channel.basic_get(queue=self._recv_queue, auto_ack=True) # 3번째꺼가 원하고자 하는 String을 가져와서 처리를 시작한다.
            if raw_data[2] is not None:
                data = raw_data[2].decode().split("|")
                data.pop()
                # print("middle data : ", data)
                result = data[1].encode() + b'|' + self._kiwoom_interact(data[0])
                print("Final Result : ", result)
                channel.basic_publish(exchange='', routing_key=self._send_queue, body=result)
                # channel.basic_get(queue=self._recv_queue, auto_ack=True)  # 작업을 끝마친 후에서야 큐에서 작업을 지운다.
            time.sleep(0.1)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QAxContainer import *
    app = QApplication(sys.argv)
    test = QueGetter()
    test.receive_data()
    app.exec_()