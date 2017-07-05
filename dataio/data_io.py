#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 18 12:10:50 2016

@author: Forever_NIP
定义连接数据库的基础操作
"""
#from StatusValue.DataBaseConnectVars import *
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
#todo remove comment
import cx_Oracle
import copy
import sys
import pandas as pd
import databasevars


class DBConnector(object):
    """
    连接数据库类
    """

    def __init__(self, connstr):
        """
        需要用连接字符串初始化
        :param connstr:  数据库连接字符串,格式：用户名／密码@ip／域名或实例名
        """

        self.connstr = connstr
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        连接数据库
        将句柄存放在类实例的属性中
        :return:
        """
        try:
            self.conn = cx_Oracle.connect(self.connstr)
            self.cursor = self.conn.cursor()
            return self.conn, self.cursor
        except:
            raise Exception("DataBase Connected Failed !")

    def disconnect(self):
        """
        断开数据库连接，关闭连接句柄
        :return:
        """
        try:
            self.cursor.close()
            self.conn.close()
        except cx_Oracle.OperationalError,exc:
            error, = exc.args
            print >> sys.stderr, "Oracle-Error-Code:", error.code
            print >> sys.stderr, "Oracle-Error-Message:", error.message

class DataLoader(object):
    """
    数据获取类

    """
    def fromfile(self, fpath, header=None, sep=','):
        """
        从文件获取
        :param fpath: 文件目录
        :param header: 第一行是否为列标题
        :param sep: 分隔符
        :return: 读取结果
        """
        exe = fpath.split('.')[-1]
        if exe == 'csv':
            res = pd.read_csv(fpath, header=header, sep=sep)
        elif exe == 'xlsx' or 'xls':
            res = pd.read_excel(fpath, header=header)
        else:
            res = pd.read_table(fpath, header=header, sep=sep)
        return res

    def fromdb(self, cursor, sql, fetchsize='all'):
        """
        从数据库获取
        :param cursor: 数据库游标
        :param sql: 获取数据sql
        :param fetchsize: 对结果的每次提取数量
        :return: 可供迭代对象，每次返回一批结果
        """
        fetcher = cursor.execute(sql)
        if fetchsize == 'all':
            res = fetcher.fetchall()
            yield res
        else:
            while True:
                result = fetcher.fetchmany(fetchsize)
                if result:
                    yield result
                else:
                    print 'data fetch finished!'
                    return


class DataSaver(object):
    """
    数据保存类

    """

    def __init__(self):
        """
        初始化
        CONNSTR：连接字符串
        db：变量，指向dbconnector类实例
        maxindex：用于设定迭代时最后一批数据的最大下标
        trytimes：用于设定当传输过程中数据库异常断开的重试次数
        """
        self.CONNSTR = None
        self.db = None
        self.maxindex = None
        self.trytimes = None

    def todb(self, CONNSTR, sql, datalist, index=0,
             fetchsize=1000, trytimes=10):
        """
        把数据存放到数据库中
        :param CONNSTR: 数据库连接字符串
        :param sql: 存放数据的sql
        sql sample:"insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) values (:1,:2,:3,:4)"
        :param datalist: 需要存放的数据
        :param index: 下标
        :param fetchsize: 每次存放的大小
        :param trytimes: 重试次数
        :return:
        """
        if self.trytimes is None:
            self.trytimes = trytimes
        self.CONNSTR = CONNSTR
        self.db = DBConnector(self.CONNSTR)
        self.db.connect()
        self.maxindex = len(datalist) - 1
        try:
            for k, i in enumerate(xrange(index, self.maxindex, fetchsize)):
                if i<index:
                    continue
                self.db.cursor.prepare(sql)
                self.db.cursor.executemany(
                    None,
                    datalist[
                        i:min(
                            i +
                            fetchsize,
                            self.maxindex)])
                self.db.conn.commit()
                print '%d rows committed sucessfully!\n' % fetchsize * (k + 1)
        except:
            if trytimes <= 0:
                tryt = copy.copy(self.trytimes)
                self.trytimes = None
                raise Exception('failed after try more than %d times' % tryt)
            else:
                self.db.disconnect()
                self.db.connect()
                self.todb(CONNSTR, sql, datalist, index=i,
                          fetchsize=fetchsize, trytimes=trytimes - 1)
        finally:
            self.db.disconnect()
        print 'insert to db sucessfully!'

    def tofile(self, filepath, datalist, mode='ab'):
        """
        将数据保存到文件中
        :param filepath: 文件地址
        :param datalist: 数据
        :param mode: 追加模式还是新增模式，默认追加模式
        :return:
        """
        with open(filepath, mode) as f:
            f.write('\n'.join(datalist))


if __name__ == '__main__':

    index = (sys.argv[1], sys.argv[2])
    connf = DBConnector(databasevars.CONNSTR)
