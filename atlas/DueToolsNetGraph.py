# -*- coding: utf-8 -*-
"""
连接潍柴toolsnet数据库，解析保存螺栓拧紧过程数据的blob字段
"""

#from StatusValue.DataBaseConnectVars import *
import cx_Oracle
import struct
import numpy as np
#import multiprocessing
import sys
import pandas as pd
#from multiprocessing import Manager
#from multiprocessing import Process

sqll = r"""
select count(distinct g."ResultID") from (
   select r3.*,rt."FinalAngle",rt."FinalTorque",rt."FinalAngleStatusID",rt."FinalTorqueStatusID" from (
        select r2.*,u."Path",u."Name" as "UnitName",u."Identifier" as "UnitIdentifier" from (
               select r1.* ,p."Name" as "ProgrameName" from (
                      select * from "Result" where "ResultStatusTypeID" in (0,1))r1
               left join "Program" p on r1."ProgramID"=p.ID) r2
        join
               (select t3.*,t4."Path" from (
                       select t1.* ,t2."ReportStructurePathID"from "Unit" t1
                       left join "SysTypeToReportStructurePath" t2
                        on t1."SystemTypeID"=t2."SystemTypeID"
                        where  t1."Name" in (u'3585-机滤器螺栓',u'3705-排气管螺栓',u'3165-Con Rod',u'3395-Cyl_Head_Main',u'3400-Cyl_Head_Auxi')
                        )t3
                left join "ReportStructurePath" t4 on t3."ReportStructurePathID"=t4.ID
                ) u on r2."UnitID"=u."ID" )r3
    left join
         "ResultTightening" rt on r3."ID"=rt."ResultID"
) fres left join "Graph" g on fres."ID"=g."ResultID"
"""


sql = """

select count(distinct g1."ResultID") from "Graph" g1
right join(
        select IDD from
       ( select * from(
        select "ID" as IDD,"UnitID" from "Result"  where "ResultStatusTypeID" in (0,1))t1
        right join
        (select * from "Unit" where  "Name" in (u'3585-机滤器螺栓',u'3705-排气管螺栓',u'3165-Con Rod',u'3395-Cyl_Head_Main',u'3400-Cyl_Head_Auxi'))t2
       on t1."UnitID"=t2."ID"))r1
on g1."ResultID"=r1."IDD"

"""


"""
连接数据库字符串
"""
CONNSTR = 'atlascopco_toolsnet' + '/' + 'T00lsNetPwd' + \
    '@' + '10.0.5.39' + '/' + 'toolsnet.weichai.com'
CONNSTR2 = 'fsideal' + '/' + 'fstest' + '@' + '60.190.243.88' + '/' + 'orcl'
CONNSTR3 = 'system' + '/' + '123456' + '@' + '10.0.8.241' + '/' + 'orcl'


def ConnectToDataBase(CONNSTR):
    """
    连接数据库方法
    :param CONNSTR: 数据库连接字符串,格式：用户名／密码@ip／域名或实例名
    :return:数据库连接句柄和游标句柄
    """
    try:
        conn = cx_Oracle.connect(CONNSTR)
        cursor = conn.cursor()
        return (conn, cursor)
    except:
        raise Exception("DataBase Connected Failed !")


def unpackvalues(blob):
    """
    解析blob字段内容（二进制转十进制）
    :param blob: blob字段内容
    :return: 解析后的结果
    """
    return np.array(
        [struct.unpack('f', blob[x:x + 4])[0]
         for x in xrange(0, len(blob), 4)]
    )


def getconnecttodb(connstr, many=10):
    """
    定义多个数据库连接
    :param connstr: 数据库连接字符串
    :param many: 连接数量
    :return: 具有many个连接数的包含数据库连接句柄和游标句柄的元组
    """
    ls = ()
    for x in range(many):
        ls.append(ConnectToDataBase(connstr))
    return ls


def mainprocessm(q, connf, connt):
    """
    多进程解析blob字段
    :param q:
    :param connf:
    :param connt:
    :return:
    """
    dic = {}
    while True:
        try:
            index = q.get(timeout=5)
            print index[0],
        except:
            connt[0].commit()
            connt[1].close()
            connt[0].close()
            connf[1].close()
            connf[0].close()
            return
        sql = 'select * from "Graph" t where "ResultID">=' + \
            str(index[0]) + ' and "ResultID"<' + str(index[1])
        excures = connf[1].execute(sql)
        valuearr = []
        for value in excures:
            # tmp=excures.fetchmany(10000)
            if value == []:
                continue
            binarydata = value[5].read()
            if value[1] in dic:
                lenth = len(binarydata) / 4
                dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]
                dic[value[1]]['times'] = np.linspace(
                    0.0, value[3] * (lenth - 1), lenth)
                values = zip(
                    [value[1]] * lenth,
                    dic[value[1]]['times'],
                    dic[value[1]][-2],
                    dic[value[1]][-1])
                if valuearr == []:
                    valuearr = np.array(values)
                else:
                    valuearr = np.concatenate([valuearr, np.array(values)])

                   # print sql
                   # resss.append([value[1],tie,angle,torque])

                dic.pop(value[1])

            else:
                dic[value[1]] = {}
                dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]

        connt[1].prepare("insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) \
        values (:1,:2,:3,:4)")
        connt[1].executemany(None, valuearr.tolist())
        connt[0].commit()


def write(valuearr, connt):
    try:
        connt[1].prepare("insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) \
 values (:1,:2,:3,:4)")

        connt[1].executemany(None, valuearr.tolist())
        connt[0].commit()
        return connt
    except:
        connt = ConnectToDataBase(CONNSTR2)
        write(valuearr, connt)


def mainprocess(index, connf, connt):
    """
    但进程解析blob字段
    :param index:
    :param connf:
    :param connt:
    :return:
    """
    dic = {}
    i = 0

    #sql='select * from "Graph" t where "ResultID">='+str(index[0])+' and "ResultID"<'+str(index[1])
    excures = connf[1].execute(sql)
    return excures.fetchall()
    valuearr = []
    for value in excures:
        # tmp=excures.fetchmany(10000)
        if i == index[0]:
            return value
        else:
            continue
        if value == []:
            connt[0].commit()
            connt[1].close()
            connt[0].close()
            connf[1].close()
            connf[0].close()
            break
        if value[5]:
            binarydata = value[5].read()

        if value[1] in dic:
            lenth = len(binarydata) / 4
            dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]
            dic[value[1]]['times'] = np.linspace(
                0.0, value[3] * (lenth - 1), lenth)
            values = zip(
                [value[1]] * lenth,
                dic[value[1]]['times'],
                dic[value[1]][-2],
                dic[value[1]][-1])
            if valuearr == []:
                valuearr = np.array(values)
            else:
                valuearr = np.concatenate([valuearr, np.array(values)])
                if len(valuearr) > 50000:
                    connt = write(valuearr, connt)
#                     try:
#                         connt[1].prepare("insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) \
#                     values (:1,:2,:3,:4)")
#
#                         connt[1].executemany(None,valuearr.tolist())
#                         connt[0].commit()
#                     except:
#                         connt=ConnectToDataBase(CONNSTR2)
#                         connt[1].prepare("insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) \
#                     values (:1,:2,:3,:4)")
#
#                         connt[1].executemany(None,valuearr.tolist())
#                         connt[0].commit()
                    valuearr = []
                # print sql
                # resss.append([value[1],tie,angle,torque])

            dic.pop(value[1])
            print i,
            i += 1

        else:
            dic[value[1]] = {}
            dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]


def mainprocesstofile(index, connf, connt):
    dic = {}
    i = 0
    sql = 'select * from "Graph" t where "ResultID">=' + \
        str(index[0]) + ' and "ResultID"<' + str(index[1])
    excures = connf[1].execute(sql)
    valuearr = []
    for value in excures:
        # tmp=excures.fetchmany(10000)
        if value == []:
            connt[0].commit()
            connt[1].close()
            connt[0].close()
            connf[1].close()
            connf[0].close()
            break

        binarydata = value[5].read()

        if value[1] in dic:
            lenth = len(binarydata) / 4
            dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]
            dic[value[1]]['times'] = np.linspace(
                0.0, value[3] * (lenth - 1), lenth)
            values = zip(
                [value[1]] * lenth,
                dic[value[1]]['times'],
                dic[value[1]][-2],
                dic[value[1]][-1])
            if valuearr == []:
                valuearr = np.array(values)
            else:
                valuearr = np.concatenate([valuearr, np.array(values)])
                if len(valuearr) > 50000:
                    pd.DataFrame(valuearr).to_csv(
                        'c:/sample.csv', mode='a', index=False, header=False)
                    valuearr = []
                # print sql
                # resss.append([value[1],tie,angle,torque])

            dic.pop(value[1])
            print i,
            i += 1

        else:
            dic[value[1]] = {}
            dic[value[1]][value[2]] = unpackvalues(binarydata) - value[4]


if __name__ == '__main__':

    index = (sys.argv[1], sys.argv[2])
    connf = ConnectToDataBase(CONNSTR)
    connt = ConnectToDataBase(CONNSTR3)
#    mainprocess(index,connf,connt)
#
#    connt[0].commit()
#    connt[1].close()
#    connt[0].close()
#    connf[1].close()
#    connf[0].close()
    mainprocess(index, connf, connt)
#    m=Manager()
#    q=m.Queue()
#    jobs=5
#    processlist=[]
#    for i in xrange(1,310988189+10,500000):
#        q.put((i,i+500000))
#    connflist=getconnecttodb(CONNSTR,jobs)
#    conntlist=getconnecttodb(CONNSTR2,jobs)
#    for i in range(jobs):
#        processlist.append(Process(target=mainprocess,args=(q,connflist[i],conntlist[i])))
#
#    for p in processlist:
#        p.start()
#    for p in processlist:
#        p.join()
#


#==============================================================================
#     dic={};i=0
#     conntools,cursortools=ConnectToDataBase(CONNSTR)
#     connlx,cursorlx=ConnectToDataBase(CONNSTR2)
#     excures=cursortools.execute('select * from "Graph" t')
#     valuearr=[]
#     for value in excures:
#         #tmp=excures.fetchmany(10000)
#         if value ==[]:
#             connlx.commit()
#             cursorlx.close()
#             cursortools.close()
#             connlx.close()
#             conntools.close()
#             break
#
#         binarydata=value[5].read()
#
#         if dic.has_key(value[1]):
#             lenth=len(binarydata)/4
#             dic[value[1]][value[2]]=unpackvalues(binarydata)-value[4]
#             dic[value[1]]['times']=np.linspace(0.0,value[3]*(lenth-1),lenth)
#             values=zip(
#                        [value[1]]*lenth,
#                        dic[value[1]]['times'],
#                        dic[value[1]][-2],
#                        dic[value[1]][-1])
#             if valuearr==[]:
#                 valuearr=np.array(values)
#             else:
#                 valuearr=np.concatenate([valuearr,np.array(values)])
#                 if len(valuearr)>5000000:
#                     cursorlx.prepare("insert into weichai_toolsnet_graph(RESULTID,SAMPLETIME,ANGLE,TORQUE) \
#                     values (:1,:2,:3,:4)")
#                     cursorlx.executemany(None,valuearr.tolist())
#                     connlx.commit()
#                     valuearr=[]
#                # print sql
#                # resss.append([value[1],tie,angle,torque])
#
#             dic.pop(value[1])
#             print i,
#             i+=1
#
#         else:
#             dic[value[1]]={}
#             dic[value[1]][value[2]]=unpackvalues(binarydata)-value[4]


#==============================================================================
