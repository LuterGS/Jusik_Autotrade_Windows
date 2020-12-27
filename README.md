Jusik_Autotrade_Windows
=======================


[Jusik_Autotrade](https://github.com/LuterGS/Jusik_Autotrade "Jusik_Autotrade")의 윈도우쪽 핸들러 프로그램입니다.
----

# Requirements
* Python (32bit, 3.6 이상 권장)
* Python 라이브러리 : pika, PyQt5 
    ```shell   
    pip install pika, pyqt5
  ```
  로 설치 가능
* 키움증권 OpenAPI 프로그램 (키움증권 홈페이지에서 설치)
* 키움증권 계좌 및 가상계좌(선택)


# How to Use
1. que_getter.py를 실행하면 됩니다.


# Warning
* 키움증권 API에서 비밀번호가 올바르지 않다 (44)는 경고 문구가 올 때가 있습니다. 그럴 땐 KOAStudio에서 접속한 뒤, 윈도우 우측 하단 아이콘에서 키움증권 API 아이콘을 찾아 비밀번호 저장 및 자동 로그인을 선택해주세요.
* 이 프로그램은 요청 데이터를 처리하기 위해 RabbitMQ를 사용하며, 해당 RabbitMQ는 Ubuntu에서 설정을 완료하고, Ubuntu의 MQ_VALUE.txt에 해당하는 내용을 사용한다고 가정합니다.
    * 즉, 다른 내용은 동일하나, Ubuntu에서의 out queue는 Windows의 in queue이고, Ubuntu에서의 in queue는 Windows의 out queue입니다.