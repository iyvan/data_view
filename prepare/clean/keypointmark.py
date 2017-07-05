# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 22:45:19 2016

@author: temp01
"""
import math
import numpy as np
from prepare.clean.dataclean import DataCleaner


class KeyPointGetter(DataCleaner):
    """
    获取数据特征点的类
    """
    def __init__(self, yieldslopemax=math.tan(math.radians(45)),
                 yieldslopemin=math.tan(math.radians(-45)),
                 breakpointcosmax=math.cos(math.radians(90)),
                 breakpointcosmin=math.cos(math.radians(175)),
                 many=5):
        """
        初始化 屈服阶段判断标准的斜率上下限，以及判断线性变化起始点的张开角度上下限
        :param yieldslopemax: 判断为屈服阶段的斜率上限
        :param yieldslopemin: 判断为屈服阶段的斜率下限
        :param breakpointcosmax: 判断为拧紧阶段（线性变化阶段）的张开角度上限
        :param breakpointcosmin: 判断为拧紧阶段（线性变化阶段）的张开角度下限
        :param many: 用来做判断的最少数据点的个数
        """
        super(KeyPointGetter, self).__init__()
        self.yieldpointslope = self.WRONGVALUE
        self.yieldslopemax = yieldslopemax
        self.yieldslopemin = yieldslopemin
        self.breakpointcos = self.WRONGVALUE
        self.breakpointcosmax = breakpointcosmax
        self.breakpointcosmin = breakpointcosmin
        self.many = many
        self.yieldpoint = self.WRONGVALUE
        self.breakpoint = self.WRONGVALUE
        self.initialpoint = self.WRONGVALUE
        self.finalpoint = self.WRONGVALUE
        self.res = self.WRONGVALUE
        self.stages = self.WRONGVALUE
        self.s1end = self.WRONGVALUE
        self.s2start = self.WRONGVALUE
        self.linearpoints1=self.WRONGVALUE
        self.linearpoints2=self.WRONGVALUE

    def getkeypoint(self, nparr_x_y, start, end, droppairs=None, reindex=True):
        """
        计算拧紧过程起始点，屈服点等特征点
        :param nparr_x_y:包含扭矩和转角的ndarray格式的数据
        :param start:参与判断的数据起始下标
        :param end:参与判断的数据结束下标
        :param droppairs:脏数据的数据起止段
        :param reindex:如果数据起止下标在脏数据段范围内，需要更改起始下标
        :return:
        """
        if end - start < 2:
            return self.WRONGVALUE
        vec = np.array(nparr_x_y[end] - nparr_x_y[start])
        matrix = nparr_x_y[start:end + 1] - nparr_x_y[start]
        self.res = self.calc_point_2_line(matrix, vec)
        if reindex and droppairs is not None:
            for v in droppairs:
                if start > v[1]:
                    continue
                if start >v[0]:
                    self.res[:v[1]-start]=0
                else:
                    self.res[v[0] - start:v[1] - start] = 0
        index = np.argmax(self.res)
        return index + start

    def checkyieldpoint(self, nparr_start_x_y, nparr_end_x_y):
        """
        计算屈服后斜率，用来判断是否有问题（是否满足屈服阶段的斜率上下限条件）
        :param nparr_start_x_y:屈服阶段起始扭矩转角
        :param nparr_end_x_y:屈服阶段结束扭矩转角
        :return:是否符合标准
        """
        vec = nparr_end_x_y - nparr_start_x_y
        self.yieldpointslope = 1.0 * vec[1] / vec[0]
        if self.yieldslopemin <= self.yieldpointslope <= self.yieldslopemax:
            return True
        else:
            return False

    def checkbreakpoint(
            self,
            nparr_start_x_y,
            nparr_breakpoint_x_y,
            nparr_end_x_y):
        """
        计算拧紧阶段转折点夹角，用来判断是否有问题
        :param nparr_start_x_y:起始阶段扭矩转角
        :param nparr_breakpoint_x_y:线性变化点（开始拧紧点）扭矩转角
        :param nparr_end_x_y:线性变化结束阶段扭矩转角
        :return:是否符合标准
        """
        a = np.linalg.norm(nparr_end_x_y - nparr_start_x_y)
        b = np.linalg.norm(nparr_end_x_y - nparr_breakpoint_x_y)
        c = np.linalg.norm(nparr_breakpoint_x_y - nparr_start_x_y)
        self.breakpointcos = (b**2 + c**2 - a**2) * 1.0 / (2 * b * c)
        if self.breakpointcosmin <= self.breakpointcos <= self.breakpointcosmax:
            return True
        else:
            return False

    def getendstartpointpairs(self, diff_nparr, nparray,
                              start, end, resultlist, endfunc='rule'):
        """
        获取干净数据的终止起始对（不包含起始，终止点）
        :param diff_nparr: ndarray格式的差值数组
        :param nparray: ndarray格式的用来计算差值的原始数据
        :param start: 需要进行判断的数据的开始下标
        :param end: 需要进行判断的数据的结束下标
        :param resultlist: 结果集
        :param endfunc: 用来找终点的方法
        :return:
        """
        endpoint = self.getstageendpoint(
            diff_nparr, start, end, many=self.many, funct=endfunc)
        if endpoint == self.WRONGVALUE:
            return
        startpoint = self.getstagestartpoint(nparray, endpoint)
        if startpoint == self.WRONGVALUE:
            return
        resultlist.append([endpoint, startpoint])
        self.getendstartpointpairs(diff_nparr, nparray,
                                   startpoint, end, resultlist,
                                   endfunc=endfunc)

    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='quick', stages=2):
        """
        获取干净数据的起始终止对（包含起始，终止点）
        :param nparr_torque:ndarray格式的扭矩数据
        :param nparr_angle:ndarray格式的转角数据
        :param finaltorque:最终扭矩
        :param finalangle:最终转角
        :param getfinalpointfunc:获取数据结束点的方法
        :param stages:分段拧紧的段数
        :return:干净数据的所有起止段
        """
        endstartlist = []
        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = self.getinitialpoint(nparr_torque)
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc)
        if stages != 1:
            self.getendstartpointpairs(
                diff_nparr,
                nparr_torque,
                self.initialpoint,
                self.finalpoint,
                endstartlist)
            endstartlist.append([self.finalpoint])
            tmp = [self.initialpoint]
            [tmp.extend(x) for x in endstartlist]
            return [(tmp[i], tmp[i + 1]) for i in range(0, len(tmp), 2)]
        else:
            return [self.initialpoint, self.finalpoint]

    def getyieldpoint(self, nparr_x_y, start, end, droppairs=None, reindex=True):
        """
        获取屈服阶段开始点的坐标
        :param nparr_x_y:ndarray格式的扭矩转角数据
        :param start:数据起始点坐标
        :param end:数据结束点坐标
        :param droppairs:垃圾数据起止坐标对
        :param reindex:是否自动校正数据起始点
        :return:屈服阶段的起始点坐标
        """
        self.getyieldpointopti(nparr_x_y, start, end, droppairs, reindex)

        if self.checkyieldpoint(nparr_x_y[self.yieldpoint], nparr_x_y[end]):
            return self.yieldpoint
        else:
            self.yieldpoint = self.WRONGVALUE
            return self.WRONGVALUE

    def getbreakpoint(self, nparr_x_y, start, end, droppairs=None, reindex=True):
        """
        获取拧紧开始阶段的数据坐标（线性变化起始点）
        :param nparr_x_y:ndarray格式的扭矩转角数据
        :param start:数据起始点
        :param end:数据结束点
        :param droppairs:垃圾数据起止坐标对
        :param reindex:是否自动矫正起始坐标点
        :return:线性变化起始点坐标（拧紧阶段起始点坐标）
        """
        breakpoint = self.getkeypoint(
            nparr_x_y, start, end, droppairs, reindex=reindex)
        # print breakpoint
        if droppairs is not None:
            nb = self.fixindroppairs(2 * breakpoint - start, droppairs)
        else:
            nb = 2 * breakpoint - start
        if nb < end and nb != self.WRONGVALUE:
            breakpoint = self.getkeypoint(
                nparr_x_y, start, nb, droppairs, reindex=reindex)
            # print breakpoint
        if breakpoint < 0:
            self.breakpoint = self.WRONGVALUE
            return self.WRONGVALUE
        if self.checkbreakpoint(
                nparr_x_y[start],
                nparr_x_y[breakpoint],
                nparr_x_y[end]):
            self.breakpoint = breakpoint
            return self.breakpoint
        else:
            self.breakpoint = self.WRONGVALUE
            return self.WRONGVALUE

    def getfeaturepoints(self, df_sample, getfinalpointfunc='quick'):
        """
        获取曲线的所有特征点
        :param df_sample:dataframe格式的扭矩转角数据
        :param getfinalpointfunc:获取曲线终点的方法
        :return:拧紧阶段起始点，屈服阶段起始点，干净数据的起止点对
        """
        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        self.keypoints = self.getstagepoints(
            nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.droppairs = self.calcdroppairs(self.keypoints)
        self.getyieldpoint(
            nparr_x_y,
            self.keypoints[1][1],
            self.finalpoint,
            self.droppairs,
            False)
        self.getbreakpoint(
            nparr_x_y,
            self.initialpoint,
            self.yieldpoint,
            self.droppairs)
        if self.breakpoint != self.WRONGVALUE:
            if nparr_torque[self.breakpoint] > 70:
                self.breakpoint = self.WRONGVALUE
        self.linearpoints1=xrange(self.keypoints[0][0],self.keypoints[0][1]+1)
        self.linearpoints2=xrange(self.keypoints[1][0],self.keypoints[1][1]+1)
        return [self.breakpoint, self.yieldpoint, self.keypoints]

    def getfeaturepointsnormal(
            self,
            df_sample,
            getfinalpointfunc='quick',
            stages=2):
        """
        获取普通螺栓（无屈服阶段）的拧紧起始点，干净数据的起止对
        :param df_sample:dataframe格式的扭矩转角数据
        :param getfinalpointfunc:获取曲线终点的方法
        :param stages:
        :return:普通螺栓（无屈服阶段）的拧紧起始点，干净数据的起止对
        """
        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        if stages == 1:
            self.keypoints = self.getstagepoints(
                nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc, stages=1)
        else:

            self.keypoints = self.getstagepoints(
                nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.getbreakpoint(nparr_x_y, self.initialpoint, self.finalpoint)
        return [self.breakpoint, self.keypoints]


#        if stage>1:
#            s1end=kpobject.s1end
#        else:
#            if yieldpoint >0:
#                s1end=yieldpoint
#            else:
#                s1end=end
#        if stage>1:
#            s2start=kpobject.keypoints[1][0]
#        else:
#            s2start=-1.0
    def getyieldpointopti(self, nparr_x_y, start, end, droppairs=None, reindex=True,times=5,lastyield=0):
        """
        获取屈服阶段起始点的迭代式算法
        当数据线性变化起始点以及数据结束点距离屈服点距离差较大时，可以采用迭代计算的方式提高精度
        不过会耗费一定的计算资源，提高的效果有限
        :param nparr_x_y:ndarray格式的扭矩转角数据
        :param start:数据起始点
        :param end:数据结束点
        :param droppairs:垃圾数据对
        :param reindex:是否自动矫正起始点
        :param times:迭代次数
        :param lastyield:上次计算出来的屈服阶段起始点
        :return:屈服阶段起始点的下标
        """
        yieldpoint = self.getkeypoint(nparr_x_y, start, end, droppairs, reindex)

        if self.checkyieldpoint(nparr_x_y[yieldpoint], nparr_x_y[end]):
            self.yieldpoint = max(lastyield,yieldpoint)
            if times>0:
                self.getyieldpointopti(nparr_x_y,2*self.yieldpoint-end,end,droppairs=droppairs,
                                       reindex=reindex,times=times-1,lastyield=self.yieldpoint)
            else:
                return self.yieldpoint
        else:
            self.yieldpoint = self.WRONGVALUE
            return self.WRONGVALUE


    def getbreakpointopti(self, nparr_x_y, start, end, droppairs=None, reindex=True,times=5):
        """
        获取线性变化阶段起始点（拧紧阶段起始点）的迭代式算法
        当数据起始点以及数据结束点（屈服阶段起始点）距离线性变化起始点（拧紧起始点）距离差较大时，可以采用迭代计算的方式提高精度
        不过会耗费一定的计算资源，提高的效果有限
        :param nparr_x_y:ndarray格式的扭矩转角数据
        :param start:数据起始点
        :param end:数据结束点
        :param droppairs:垃圾数据对
        :param reindex:是否自动矫正起始点
        :param times:迭代次数
        :return:线性变化阶段（拧紧阶段）起始点的下标
        """
        self.breakpoint = self.getkeypoint(
            nparr_x_y, start, end, droppairs, reindex=reindex)
        # print breakpoint
        if times>0:
            sb=self.breakpoint-start
            be=end-self.breakpoint
            if sb < be:
                tmp=start
                if droppairs is not None:
                    nb = self.fixindroppairs(2 * self.breakpoint - tmp, droppairs)
                else:
                    nb = 2 * self.breakpoint - tmp
                if nb < end and nb != self.WRONGVALUE:
                     self.getbreakpointopti(
                        nparr_x_y, start, nb, droppairs, reindex=reindex,times=times-1)
            elif sb>be:
                # if droppairs is not None:
                #     end = self.fixindroppairs(end, droppairs)
                #     start=self.fixindroppairs(2*self.breakpoint-end,droppairs)
                # else:
                start=2*self.breakpoint-end
                if  start != self.WRONGVALUE and end != self.WRONGVALUE:
                    self.getbreakpointopti(
                        nparr_x_y, start, end, droppairs, reindex=reindex, times=times - 1)
            else:
                self.getbreakpointopti(
                    nparr_x_y, start, end, droppairs, reindex=reindex, times=-1)
                # print breakpoint
        else:
            if self.breakpoint < 0:
                self.breakpoint = self.WRONGVALUE
                return self.WRONGVALUE
            if not self.checkbreakpoint(
                    nparr_x_y[start],
                    nparr_x_y[self.breakpoint],
                    nparr_x_y[end]):
                self.breakpoint = self.WRONGVALUE
                return self.WRONGVALUE
            else:
                return self.breakpoint
