#!/usr/bin/python
# coding=UTF-8

import uuid
import time
import pymysql
from config import Common

show_logger = False


# 日志打印信息
def logger(content):
    if show_logger:
        now_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(now_date, '-', content)


class MysqlService:

    def __init__(self):
        # self.host = '127.0.0.1'
        self.host = '192.168.1.208'
        self.port = 3306
        self.user = 'test'
        self.password = '123456'
        self.database = 'auto_test_db'

    # 生成主键
    @staticmethod
    def get_id():
        return str(uuid.uuid1()).upper()

    # 初始化MySQL数据库连接
    def __mysql_init(self):
        db = None
        try:
            db = pymysql.connect(host=self.host, user=self.user,
                                 password=self.password, database=self.database)
        except Exception as e:
            print('初始化MySQL数据库链接异常:', e)
        return db

    # 关闭连接
    @staticmethod
    def __mysql_close(db=None, cursor=None):
        if cursor is not None:
            cursor.close()
        if db is not None:
            db.close()

    # 检查数据库连接
    def check_connect(self):
        result = False
        db = None
        try:
            db = pymysql.connect(self.host, self.user, self.password, self.database)
            result = True
        except Exception as e:
            pass
        finally:
            if db is not None:
                db.close()
        logger("check_mysql_connect: %s" % result)
        return result

    # 查询测试报告
    def select_report(self):
        res_data = ()
        db = None
        cursor = None
        try:
            db = self.__mysql_init()
            cursor = db.cursor()
            sql = "select * from t_1000_report"
            logger(sql)
            cursor.execute(sql)
            res_data = cursor.fetchall()
        except Exception as e:
            print('查询查询测试报告异常，回滚:', e)
        finally:
            self.__mysql_close(db=db, cursor=cursor)
        return res_data

    # 添加测试报告信息
    def insert_report(self, device_id, device_name):
        t_id = self.get_id()
        db = None
        cursor = None
        try:
            db = self.__mysql_init()
            cursor = db.cursor()
            sql = "INSERT INTO t_1000_report (t_id, t_device_id, t_device_name, t_crate_time) " \
                  "VALUES ('%s', '%s', '%s', now())" % (t_id, device_id, device_name)
            logger(sql)
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            print('添加测试报告信息异常，回滚:', e)
        finally:
            self.__mysql_close(db=db, cursor=cursor)
        return t_id

    # 添加测试报告详细信息
    def insert_report_detail(self, report_id, temperature, test_unit_name, test_unit_result, test_unit_fail):
        t_id = self.get_id()
        db = None
        cursor = None
        try:
            db = self.__mysql_init()
            cursor = db.cursor()
            state = 0
            if len(test_unit_fail) > 0:
                state = 1
            sql = "INSERT INTO t_1001_report_detail (t_id, t_report_id, t_temperature, t_test_unit_name, " \
                  "t_test_unit_result, t_test_unit_fail, t_state, t_create_time) " \
                  "VALUES ('%s', '%s', '%s', '%s','%s', '%s','%s',now())" % (t_id, report_id, temperature,
                                                                        test_unit_name, test_unit_result,
                                                                        state, test_unit_fail)
            logger(sql)
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            print('添加测试报告详细信息异常，回滚:', e)
        finally:
            self.__mysql_close(db=db, cursor=cursor)
        return t_id

    # 更细测试耗时时间
    def update_test_time(self, report_id, test_time, state):
        db = None
        cursor = None
        try:
            db = self.__mysql_init()
            cursor = db.cursor()
            sql = "UPDATE t_1000_report SET t_test_time='%s', t_state='%s' WHERE t_id='%s'" % (test_time, state,
                                                                                               report_id)
            logger(sql)
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            print('更细测试耗时时间异常，回滚:', e)
        finally:
            self.__mysql_close(db=db, cursor=cursor)


class TestReport:

    def __init__(self):
        self.ms = MysqlService()

    # 添加主表报告
    def inset_report(self, device_id="", device_name=""):
        res_id = ""
        try:
            # 判断mysql服务是否可用
            if self.ms.check_connect():
                res_id = self.ms.insert_report(device_id=device_id, device_name=device_name)
        except Exception as e:
            print(e)
        return res_id

    # 添加报告详情信息
    def insert_report_detail(self, report_id, temperature, test_unit_name):
        try:
            # 判断mysql服务是否可用
            if self.ms.check_connect():
                test_unit_result = Common.test_report
                test_unit_fail = Common.test_error_report
                self.ms.insert_report_detail(report_id, temperature, test_unit_name,
                                             test_unit_result, test_unit_fail)
        except Exception as e:
            print(e)

    # 更新测试耗时时间
    def update_test_time(self, report_id, test_time):
        try:
            state = 0
            if len(Common.error_record) > 0:
                state = 1

            # 判断mysql服务是否可用
            if self.ms.check_connect():
                self.ms.update_test_time(report_id=report_id, test_time=test_time, state=state)
        except Exception as e:
            print(e)


# tr = TestReport()
# print(ms.check_connect())
# id = tr.inset_report(device_id="12a3sdf12d3sa", device_name="IM218")
# id = "30DE4162-13E7-11E9-86B9-005056C00008"
# tr.update_test_time(id, 100)
# data = ms.select_report()
# print(data)

# MysqlService().select_report()
