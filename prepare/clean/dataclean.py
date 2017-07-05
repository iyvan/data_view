# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 22:42:01 2016

@author: temp01
"""
import numpy as np
from prepare.clean.basecalc import BaseCalc


class DataCleaner(BaseCalc):

    def __init__(self):

        super(DataCleaner, self).__init__()
        pass

    def selectfromdeepv(self,nparr_torque,endstartlist,max=2,how='depth'):
        """
        从获取V型曲线的结果列表中筛选深度最深的几个V型曲线，作为垃圾数据，比如，两段拧紧需要找最深的1个V型曲线，
        三段拧紧需要找最深的2个V型曲线。
        :param nparr_torque: ndarray 格式的扭矩数据
        :param endstartlist: 利用checkdeepv方法获得的结果
        :param max: 定义获取最深的几个
        :param how:目前未使用
        :return:最深的几个V型曲线起始结束点
        """
        tmp=[]
        for v in endstartlist:
            tmp.append(np.max(nparr_torque[v[0]:v[1]+1])-np.min(nparr_torque[v[0]:v[1]+1]))
        args=np.argsort(tmp)[-1*max:]
        args.sort()
        return (np.array(endstartlist)[args]).tolist()

    def fixindroppairs(self, x, droppairs):
        """
        获取线性变化点时，如果需要迭代计算，则需要重新选择第一次计算的线性变化点两边的线条长度
        这时候可能遇到两边取点取到垃圾数据上点情况，这个时候需要一个方法获取到干净的数据点上
        :param x:需要选取的线段长度
        :param droppairs:垃圾数据起止列表
        :return:对应的干净数据下标值
        """
        for v in droppairs:
            if v[0] <= x <= v[1]:
                return self.fixindroppairs(v[1] + 1, droppairs)
        return x

    def joinpairs(self, pairslist):
        """
        用数据清洗算法清洗数据时可能会产生形如：[[1,9][9,19],[29,33],[33,37],[40,50]]的起止列表，这个时候需要进行合并
        合并结果为[[1,19],[29,37],[40,50]]
        本方法是完成上述过程的
        :param pairslist: 需要join的数值对
        :return: join后的结果
        """
        if len(pairslist) < 2:
            return pairslist
        res = []
        tmp = pairslist.pop(0)
        x1, y1 = tmp[0], tmp[1]
        while pairslist:
            tmp = pairslist.pop(0)
            x2, y2 = tmp[0], tmp[1]
            if y1 == x2:
                x1, y1 = x1, y2
            else:
                res.append([x1, y1])
                x1, y1 = x2, y2
        res.append([x1, y1])
        return res

    def calcdroppairs(self, pairslist):
        """
        由干净的数据起止对，计算出垃圾数据起止对
        :param pairslist: 干净数据的开始和结束坐标对
        :return: 垃圾数据的开始和结束坐标对
        """
        res = []
        for i, v in enumerate(pairslist):

            if i == 0:
                x0 = v[1]
            else:
                x1 = v[0]
                res.append((x0, x1))
                x0 = v[1]
        return res

    def clean_droppairs(self, droppairs, yieldpoint, stages=3):
        """
        获取屈服点之前的垃圾数据起止对
        :param droppairs: 垃圾数据起止对
        :param yieldpoint: 屈服点
        :param stages: 获取的段数
        :return: 屈服点之前的垃圾数据起止对列表
        """
        cleanresult = []
        for v in droppairs:
            if yieldpoint > v[1]:
                cleanresult.append(v)

        return cleanresult[-1 * (stages - 1):]

    def clean_droppairsbyrule(
            self,
            droppairs,
            nparr_torque,
            nparr_angle,
            stages=3):
        """
        通过规则获取需要丢弃的垃圾数据起止对（根据扭矩的变化除以转角的变化的大小来确定）
        :param droppairs:所有的垃圾数据起止对
        :param nparr_torque:ndarray格式的扭矩数据
        :param nparr_angle:ndarray格式的转角数据
        :param stages:需要多少段
        :return:需要丢弃的垃圾数据起止对
        """
        anglediff = np.array(
            map(lambda x: nparr_angle[x[1]] - nparr_angle[0], droppairs))
        torquediff = np.array(map(lambda x: np.max( nparr_torque[x[0]:x[1] + 1]) -
                                  np.min(nparr_torque[x[0]:x[1] + 1]), droppairs))
        a, b = np.argsort(torquediff * 1.0 /
                          np.abs(anglediff))[-1 * (stages - 1):]
        if droppairs[a][1] < droppairs[b][1]:
            return [droppairs[a], droppairs[b]]
        else:
            return [droppairs[b], droppairs[a]]

    def checkpointsif(self, nparray, calcmarker, number):
        """
        判断数组数值是否满足某个条件
        :param nparray: 需要进行判断的ndarray格式数据
        :param calcmarker:判断符号
        :param number:数组与之对比的数字
        :return:数组内数字是否都符合对比条件
        """
        if len(nparray) == 0:
            raise Exception('nparry is empty!')
        if calcmarker == '>':
            return (nparray > number).all()
        elif calcmarker == '>=':
            return (nparray >= number).all()
        elif calcmarker == '<':
            return(nparray < number).all()
        elif calcmarker == '<=':
            return (nparray <= number).all()
        elif calcmarker == '=':
            return (nparray == number).all()
        else:
            raise Exception('clacmarker: %s is not defined!' % calcmarker)

    def checkdeepv(self, diff_nparr, nparr_torque, deep=3):
        """
        获取曲线的深v点，你懂的，起始点，最低点，结束点（值大于起始点）
        :param diff_nparr:扭矩变化数组（做差值）
        :param nparr_torque: 扭矩数组
        :param deep:V型曲线的最小深度标准
        :return:获取的V型曲线的起止对
        """
        d = 0
        u = 0
        res = []
        tmp = []
        for i, v in enumerate(diff_nparr):
            if v <= 0 and d == 0 and u == 0:
                tmp.append(i - 1)
                d += 1
            elif v <= 0 and d != 0 and u == 0:
                d += 1
            elif v <= 0 and d == 0 and u != 0:
                raise Exception('error!!!')
            elif v <= 0 and d != 0 and u != 0:
                tmp = []
                tmp.append(i - 1)
                d = 1
                u = 0
            elif v > 0 and d == 0 and u == 0:
                pass
            elif v > 0 and d != 0 and u == 0:
                if d >= deep:
                    tmp.append(i - 1)
                    u += 1
                else:
                    d = 0
                    tmp = []
            elif v > 0 and d == 0 and u != 0:
                raise Exception('error!!!')
            else:
                u += 1
                if nparr_torque[i] >= nparr_torque[tmp[0]]:
                    tmp.append(i)
                    res.append(tmp)
                    u = 0
                    d = 0
                    tmp = []
        if tmp != []:
            tmp.append(len(diff_nparr) - 1)
            res.append(tmp)
        return res
#    @runtimecheck

    def checkdeepvplus(self, diff_nparr, nparr_torque,
                       start, end, deep=5, restype='joinpairs'):

        """
        获取V型曲线的起止点的升级版
        :param diff_nparr:扭矩变化数组（做差值）
        :param nparr_torque:扭矩数组
        :param start:起始点
        :param end:结束点
        :param deep:最小深度标准
        :param restype:结果类型
            joinpairs:join后的结果
            pairs：原始结果
        :return:曲线的起止结果对
        """
        d = 0
        res = []
        tmp = []
        diffsum = []
        for i, v in enumerate(diff_nparr[start:end + 1]):

            if v < 0 and d == 0:
                d += 1
                tmp.append(i - 1 + start)
                diffsum.append(v)
            elif d != 0:
                diffsum.append(v)
                d += 1
                if sum(diffsum) > 0 and d >= deep:
                    tmp.append(np.argmin(np.cumsum(diffsum)) + tmp[0] + 1)
                    tmp.append(i + start)
                    res.append(tmp)
                    d = 0
                    tmp = []
                    diffsum = []
                elif sum(diffsum) > 0 and d < deep:
                    tmp = []
                    d = 0
                    diffsum = []
                else:
                    pass

            else:
                pass
        if tmp != []:
            tmp.append(np.argmin(np.cumsum(diffsum)) + tmp[0] + 1)
            tmp.append(end)
            res.append(tmp)
        if restype == 'pairs':
            return [[x[0], x[2]] for x in res]
        elif restype == 'joinpairs':
            return self.joinpairs([[x[0], x[2]] for x in res])
        else:
            return res

    def getpointbyrule(self, diffnparray, start, rule, many=5, offset=-1):
        """
        获取曲线开始变化的点
        :param diffnparray: ndarray格式的差值结果
        :param start: 起始点下标
        :param rule:变化规则
        :param many: 连续多少个点符合该规则
        :param offset: 结果偏移量
        :return: 符合该规则的第一点的坐标
        """
        if rule == '<':
            mapper = lambda x: x < 0
        elif rule == '>':
            mapper = lambda x: x > 0
        elif rule == '<=':
            mapper = lambda x: x <= 0
        elif rule == '>=':
            mapper = lambda x: x >= 0
        else:
            raise Exception('Rule: %s is not defined!' % rule)

        for i, x in enumerate(diffnparray[start:]):
            if mapper(x):
                # if
                # self.checkpointsif(diffnparray[i+start:i+start+many],rule,0):
                if self.checkpointsif(
                    np.cumsum(
                        diffnparray[
                            i +
                            start:i +
                            start +
                            many]),
                        rule,
                        0):
                    return i + start + offset
        return self.WRONGVALUE

    def getinitialpoint(self, nparr_torque, start=0, many=5):
        """
        计算有效数据开始点
        :param nparr_torque: 扭矩数据
        :param start: 开始判断的点坐标
        :param many: 连续上升点的个数下限
        :return: 起始点坐标
        """
        # lenth=len(nparr_torque)-2
        for i, v in enumerate(nparr_torque[start:]):
            if v > 0:
                return i
#            if v>0 and i+start<lenth-many:
#
#                if (((nparr_torque[i+1+start:i+many+1+start]-v)>0).all()) and \
#                    (self.calcslope(nparr_torque,nparr_angle,i+start,i+start+many+1)<3.7):
#                    return i

    def getfinalpoint(
            self,
            diff_nparr,
            nparr_torque,
            nparr_angle=None,
            finaltorque=None,
            finalangle=None,
            funct='quick',
            many=5,
            maxdiff=0.1
            ):
        """
        计算曲线终点
        :param diff_nparr:差值结果
        :param nparr_torque:ndarray格式的扭矩数据
        :param nparr_angle:ndarray格式的转角数据
        :param finaltorque:最终扭矩
        :param finalangle:最终转角
        :param funct:计算终点的方法
        :param many:方法中需要连续多少个点满足条件的阈值
        :param maxdiff:扭矩下降比例的阈值
        :return:终点坐标
        """

        if funct == 'comparison' and finaltorque is not None and finalangle is not None:
            ftmax = finaltorque + 0.01
            ftmin = finaltorque - 0.01
            famax = finalangle + 0.01
            famin = finalangle - 0.01
            return np.argmax(
                ((nparr_torque < ftmax) & (
                    nparr_torque > ftmin)) & (
                    (nparr_angle < famax) & (
                        nparr_angle > famin)))
        elif funct == 'max':
            maxindextor = np.argmax(nparr_torque)
            maxindexang = np.argmax(nparr_angle)
            if maxindexang == maxindextor:
                return maxindextor
            else:
                for i, v in enumerate(nparr_torque[maxindextor:]):
                    if ((nparr_torque[
                            maxindextor + i + 1:maxindextor + i + many + 1] - v) < 0).all():
                        return i
                return self.WRONGVALUE
        elif funct == 'quick':
            return np.argmax(-1.0 * diff_nparr[1:] * nparr_torque[:-1]) - 1
        elif funct == 'maxnoyield':
            return np.argmax(nparr_torque)
        elif funct == 'maxyield':
            id1=np.argmax(nparr_torque)
            id2=np.argmax(nparr_angle)
            if id1==id2:
                return id1
            elif id2>id1:
                if np.abs(nparr_torque[id1]-nparr_torque[id2])*1.0/nparr_torque[id1]<maxdiff:
                    return id2
                else:
                    res= id1+np.argmax(diff_nparr[id1:id2+1]*-1.0)-2
                    return res

            else:
                return id2

        else:
            raise Exception('funct: %s is not defined!' % funct)

    def getstagestartpoint(self, nparray, start):
        """
        计算分步拧紧，第二个阶段以后的每段起始点
        :param nparray: ndarray格式的扭矩或转角数据
        :param start: 起始点坐标
        :return: 每段有效数据的起始点
        """
        if start >= len(nparray) - 1:
            return self.WRONGVALUE
        nparrayt = nparray[start:] > nparray[start]
        index = nparrayt.argmax()
        if index == 0:
            return self.WRONGVALUE
        else:
            return start + index

    def getstageendpoint(self, diff_nparr, start, end,
                         many=5, funct='rule'):
        """
        计算每段数据结束点
        funct: 'rule','deepv'
        :param diff_nparr: 差值结果
        :param start: 起始点坐标
        :param end:结束点坐标
        :param many:符合判断规则的点的数量阈值
        :param funct:判断规则
        :return:数据结束点坐标
        """
        if start >= end:
            return self.WRONGVALUE
        if funct == 'rule':
            return self.getpointbyrule(
                diff_nparr[
                    :end],
                start,
                rule='<',
                many=many,
                offset=-1)
