# main.py -- put your code here!

import _thread
import test_startup

_thread.start_new_thread(test_startup.run, ())  # 启动测试程序
_thread.start_new_thread(test_startup.CanM().recv_can, ())  # 启动can数据接收刷新程序




