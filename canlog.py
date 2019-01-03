# main.py -- put your code here!


import can
import time

class CanM:
    def __init__(self):
        can.rc['interface'] = 'socketcan'
        can.rc['channel'] = 'can0'
        self.can_bus = can.interface.Bus()

    # 发送can信息
    def send_can(self, can_id=None, can_data=None, extended_id=False):
        try:
            msg = can.Message(arbitration_id=can_id, data=bytearray.fromhex(can_data), extended_id=extended_id)
            self.can_bus.send(msg)
            time.sleep(0.001)
            print("can信息发送:", time.time(), can_id, '#', can_data)
        except Exception as e:
            print(e)

    # 接收can信息
    def recv_can(self):
        try:
            while True:
                bo = self.can_bus.recv(timeout=10)
                if bo is not None:
                    frame_id = bo.arbitration_id
                    data = (bo.data + bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))[:8]
                    Common.can_recv_dict[frame_id] = data
                    print("can data: ", data)
                    time.sleep(0.01)
        except Exception:
            Common.error_record['Can'] = "can connect error"
            time.sleep(5)
            print("restart connect recv can")
            self.recv_can()




