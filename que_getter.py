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




class QueGetter:

    get_mq_val = GET_MQ_VALUE()
    _url = get_mq_val["MQ_URL"]
    _port = get_mq_val["MQ_PORT"]
    _vhost = get_mq_val["MQ_VHOST"]
    _cred = pika.PlainCredentials(get_mq_val["MQ_ID"], get_mq_val["MQ_PW"])
    _send_queue = get_mq_val["MQ_OUT_QUEUE"]
    _recv_queue = get_mq_val["MQ_IN_QUEUE"]

    def __init__(self):
        # 키움증권 로딩
        self._kiwoom = kiwoom_main.TextKiwoom()
        self.FUNC = [
            self._kiwoom.get_balance,
            self._kiwoom.get_min_past_data,
            self._kiwoom.get_highest_trade_amount_jusik,
            self._kiwoom.trade_jusik,
            self._kiwoom.trade_jusik,
            self._kiwoom.get_profit,
            self._kiwoom.get_jogunsik_value,
            self._kiwoom.program_restart,
            self._kiwoom.get_day_past_data,
            self._kiwoom.get_jisu_day_past_data
        ]

        self.conn = pika.BlockingConnection(pika.ConnectionParameters(self._url, int(self._port), self._vhost, self._cred))
        channel = self.conn.channel()

        # 기본적으로 돌아가는 consumer, callback 설정
        channel.basic_consume(
            queue=self._recv_queue,
            on_message_callback=lambda ch, deli, prop, val:
                self.receive_data(ch, deli, prop, val, self._send_queue),
            auto_ack=True
        )
        channel.start_consuming()

    def kiwoom_interact(self, func_value):

        # 프로그램의 모든 인자는 Linux에서 넘겨준다
        # 여기서는 인자를 해석해 맞는 function에 넣는 역할만 한다.
        # func_value는 순서대로 요청 함수번호, 함수인자1, 함수인자2... 의 형식으로 온다.
        # 즉, func_value[0]은 함수 번호를 의미한다.

        func_value = func_value.split(",")
        func_value[0] = int(func_value[0])
        return self.FUNC[func_value[0]](func_value)

    def receive_data(self, channel, deliver_info, properties, value :bytes, send_queue):
        value = value.decode().split("|")
        print(str(datetime.datetime.now()), "\t요청받은 pid : ", value[0], "\t요청받은 항목 : ", value[1])
        kiwoom_result = self.kiwoom_interact(value[1])
        final_result = value[0].encode() + b"|" + kiwoom_result
        channel.basic_publish(exchange='', routing_key=send_queue, body=final_result)

        # 만약 프로그램이 종료되어야 할 때
        try:
            if kiwoom_result[0] == 33:
                print(kiwoom_result[1:].decode() + "초 만큼 쉽니다.")
                time.sleep(int(kiwoom_result[1:].decode()))
                exit(1)
        except IndexError:
            else_func.timelog("문제 발생! : ", kiwoom_result)
            exit(1)


if __name__ == "__main__":
    while True:
        process1 = Process(target=start_program, args=())
        process1.start()
        process1.join()
