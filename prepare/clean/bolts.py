# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 22:47:56 2016

@author: temp01
定义不同螺栓清洗数据及提取特征点数据的类，每个类对应一种螺栓+拧紧过程
视情况，主要实现：
        getinitialpoint(获取数据起始点)
        getstagepoints（获取数据中，有效数据的所有起始，结束段，例如：（（30，90），（120，340））表示0-30为垃圾数据，90-120为垃圾数据，340-为垃圾数据）
        getfeaturepoints（获取数据中的一些特征点，包括每段有效数据的起始，结束点，开始线性变化的点，开始屈服的点）
"""
from prepare.clean.keypointmark import KeyPointGetter
import numpy as np

class ConRodGetter(KeyPointGetter):
    """
    定义ConRond螺栓的数据清洗及特征提取类
    """
    def __init__(self):

        super(ConRodGetter, self).__init__()
        self.keypoints = []
        self.endstartlist = None
        self.droppairs = None

    def getinitialpoint(self, nparr_torque):
        """
        获取干净数据的起始点
        :param nparr_torque: ndarray格式的扭矩数据
        :return:数据起始点的坐标（从0开始计算）
        """
        inip = self.getpointbyrule(nparr_torque, 0, '>', many=40, offset=0)
        if 0 < inip < 150:
            if nparr_torque[inip + 40] - nparr_torque[inip] < 10:
                inip = self.getpointbyrule(
                    nparr_torque[150:],
                    0,
                    '>',
                    many=40,
                    offset=0) + 150
        return inip

    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='quick'):
        """
        获取所有有效数据段的起始，结束点
        :param nparr_torque: ndarray格式的扭矩数据
        :param nparr_angle: ndarray格式的转角数据
        :param finaltorque: 最终扭矩
        :param finalangle: 最终转角
        :param getfinalpointfunc: 获取干净数据终点的方法
        :return: 所有有效数据段的起始，结束点列表
        """
        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = self.getinitialpoint(nparr_torque)
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc)
        # self.getendstartpointpairs(diff_nparr,nparr_torque,self.initialpoint,self.finalpoint,endstartlist)
        self.endstartlist = self.checkdeepvplus(
            diff_nparr, nparr_torque, self.initialpoint, self.finalpoint)
        self.endstartlist.append([self.finalpoint])
        tmp = [self.initialpoint]
        [tmp.extend(x) for x in self.endstartlist]
        return [(tmp[i], tmp[i + 1]) for i in range(0, len(tmp), 2)]

    def getfeaturepoints(self, df_sample, getfinalpointfunc='quick'):
        """
        获取曲线的特征点
        :param df_sample: dataframe格式的数据，包含angle和torque两个列名，并且分别存放的是角度和扭矩的值
        :param getfinalpointfunc: 获取曲线终点的方法
        :return: 将所有特征点分别保存至实例的属性中
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
            True)
        if self.yieldpoint > 0:
            self.droppairs = self.clean_droppairs(
                self.droppairs, self.yieldpoint)
        else:
            self.droppairs = self.clean_droppairsbyrule(
                self.droppairs, nparr_torque, nparr_angle)
        self.stages = []
        x0 = self.initialpoint
        for v in self.droppairs:
            self.stages.append([x0, v[0]])
            x0 = v[1]
        if self.yieldpoint > 0:
            self.stages.append([x0, self.yieldpoint])
            self.stages.append([self.yieldpoint, self.finalpoint])
        else:
            self.stages.append([x0, self.finalpoint])

        self.getbreakpoint(
            nparr_x_y,
            self.initialpoint,
            self.yieldpoint,
            self.droppairs)
        if self.breakpoint != self.WRONGVALUE:
            if nparr_torque[self.breakpoint] > 70:
                self.breakpoint = self.WRONGVALUE

        self.linearpoints1 = []
        for v in self.stages:
            for x in range(v[0], v[1] + 1):
                self.linearpoints1.append(x)
        self.s1end = self.yieldpoint
        self.s2start = self.yieldpoint



class JilvqiGetter(KeyPointGetter):
    """
    参考ConRodGetter类
    """
    def __init__(self):

        super(JilvqiGetter, self).__init__()
        self.keypoints = []
        self.endstartlist = None
        self.droppairs = None

    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='quick', stages=2):

        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = self.getinitialpoint(nparr_torque)
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc)
        self.s1end=self.getstageendpoint(diff_nparr,self.initialpoint,
                                         self.finalpoint,many=8)
        self.s2start=self.getstagestartpoint(nparr_torque,self.s1end)
        return [[self.initialpoint,self.s1end],[self.s2start,self.finalpoint]]

    def getfeaturepoints(self, df_sample, getfinalpointfunc='maxnoyield'):

        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        self.keypoints = self.getstagepoints(
            nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.stages=self.keypoints
        self.linearpoints1=xrange(self.initialpoint,self.s1end+1)
        self.linearpoints2=xrange(self.s2start,self.finalpoint+1)
        self.droppairs = self.calcdroppairs(self.keypoints)
        self.getbreakpoint(nparr_x_y,self.initialpoint,self.s1end)
        return self.keypoints







class PaiqiguanGetter(KeyPointGetter):
    """
    参考ConRodGetter类
    """
    def __init__(self):

        super(PaiqiguanGetter, self).__init__()
        self.keypoints = []
        self.endstartlist = None
        self.droppairs = None

    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='quick', stages=2):

        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = self.getinitialpoint(nparr_torque)
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc)
        self.s1end=self.WRONGVALUE
        self.s2start=self.WRONGVALUE
        return [[self.initialpoint,self.finalpoint]]

    def getfeaturepoints(self, df_sample, getfinalpointfunc='maxnoyield'):

        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        self.keypoints = self.getstagepoints(
            nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.stages=self.keypoints
        self.linearpoints1=xrange(self.initialpoint,self.finalpoint)
        self.linearpoints2=self.WRONGVALUE
        self.droppairs = self.WRONGVALUE
        self.breakpoint=self.WRONGVALUE
        return self.keypoints



class CylheadmainGetter(KeyPointGetter):
    """
    参考ConRodGetter类
    """
    def __init__(self):

        super(CylheadmainGetter, self).__init__()
        self.keypoints = []
        self.endstartlist = None
        self.droppairs = None

    def getinitialpoint(self, nparr_torque,nparr_angle,many=20,toptor=20):
        inip=self.WRONGVALUE
        dist=self.calcdistance(nparr_angle,nparr_torque)
        # for i in xrange(len(nparr_torque)):
        #     if (nparr_angle[i+1:i+many]>nparr_angle[i]).all():
        #         inip=i
        #         return inip
        for i,x in enumerate(nparr_angle):
            if x>0 and (dist[i:i+many]<10).all():
                inip=i
                return inip
        return inip

    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='maxyield'):

        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = self.getinitialpoint(nparr_torque,nparr_angle)
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            nparr_angle,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc)
        #self.finalpoint=np.argmax(nparr_angle)
        # self.getendstartpointpairs(diff_nparr,nparr_torque,self.initialpoint,self.finalpoint,endstartlist)
        self.endstartlist = self.checkdeepvplus(
            diff_nparr, nparr_torque, self.initialpoint, self.finalpoint)
        self.endstartlist=self.selectfromdeepv(nparr_torque,self.endstartlist)

        self.endstartlist.append([self.finalpoint])
        tmp = [self.initialpoint]
        [tmp.extend(x) for x in self.endstartlist]
        return [(tmp[i], tmp[i + 1]) for i in range(0, len(tmp), 2)]

    def getfeaturepoints(self, df_sample, getfinalpointfunc='maxyield'):
        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        self.keypoints = self.getstagepoints(
            nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.droppairs = self.calcdroppairs(self.keypoints)
        self.getyieldpoint(
            nparr_x_y,
            self.keypoints[-1][0],
            self.finalpoint,
            self.droppairs,
            True)
        # self.yieldpoint=self.getyieldpoint(nparr_x_y,2*self.yieldpoint-self.finalpoint,
        #                                    self.finalpoint,self.droppairs,True)
        if self.yieldpoint > 0:
            self.droppairs = self.clean_droppairs(
                self.droppairs, self.yieldpoint)
        # else:
        #     self.droppairs = self.clean_droppairsbyrule(
        #         self.droppairs, nparr_torque, nparr_angle)
        self.stages = []
        x0 = self.initialpoint
        for v in self.droppairs:
            self.stages.append([x0, v[0]])
            x0 = v[1]
        if self.yieldpoint > 0:
            self.stages.append([x0, self.yieldpoint])
            self.stages.append([self.yieldpoint, self.finalpoint])
        else:
            self.stages.append([x0, self.finalpoint])

        self.getbreakpoint(
            nparr_x_y,
            self.initialpoint,
            self.keypoints[0][1],
            self.droppairs)
        if self.breakpoint != self.WRONGVALUE:
            if nparr_torque[self.breakpoint] > 70:
                self.breakpoint = self.WRONGVALUE

        self.linearpoints1 = []
        for v in self.stages:
            for x in range(v[0], v[1] + 1):
                self.linearpoints1.append(x)
        self.s1end = self.yieldpoint
        self.s2start = self.yieldpoint



class CylheadauxiGetter(KeyPointGetter):
    """
    参考ConRodGetter类
    """
    def __init__(self):

        super(CylheadauxiGetter, self).__init__()
        self.keypoints = []
        self.endstartlist = None
        self.droppairs = None


    def getstagepoints(self, nparr_torque, nparr_angle, finaltorque=None,
                       finalangle=None, getfinalpointfunc='maxyield'):

        diff_nparr = self.calcdiff(nparr_torque)
        self.initialpoint = 1
        self.finalpoint = self.getfinalpoint(
            diff_nparr,
            nparr_torque,
            nparr_angle,
            finaltorque,
            finalangle,
            funct=getfinalpointfunc,
            maxdiff=0.05)
        # self.finalpoint=np.argmax(nparr_angle)
        # self.getendstartpointpairs(diff_nparr,nparr_torque,self.initialpoint,self.finalpoint,endstartlist)
        self.endstartlist = self.checkdeepvplus(
            diff_nparr, nparr_torque, self.initialpoint, self.finalpoint)
        self.endstartlist = self.selectfromdeepv(nparr_torque, self.endstartlist,1)

        self.endstartlist.append([self.finalpoint])
        tmp = [self.initialpoint]
        [tmp.extend(x) for x in self.endstartlist]
        return [(tmp[i], tmp[i + 1]) for i in range(0, len(tmp), 2)]

    def getfeaturepoints(self, df_sample, getfinalpointfunc='maxyield'):
        nparr_x_y = df_sample[['angle', 'torque']].values
        nparr_torque = df_sample.torque.values
        nparr_angle = df_sample.angle.values
        self.keypoints = self.getstagepoints(
            nparr_torque, nparr_angle, getfinalpointfunc=getfinalpointfunc)
        self.droppairs = self.calcdroppairs(self.keypoints)
        self.getyieldpoint(
            nparr_x_y,
            self.keypoints[-1][0],
            self.finalpoint,
            self.droppairs,
            True)
        # self.yieldpoint=self.getyieldpoint(nparr_x_y,2*self.yieldpoint-self.finalpoint,
        #                                    self.finalpoint,self.droppairs,True)
        if self.yieldpoint > 0:
            self.droppairs = self.clean_droppairs(
                self.droppairs, self.yieldpoint)
        # else:
        #     self.droppairs = self.clean_droppairsbyrule(
        #         self.droppairs, nparr_torque, nparr_angle)
        self.stages = []
        x0 = self.initialpoint
        for v in self.droppairs:
            self.stages.append([x0, v[0]])
            x0 = v[1]
        if self.yieldpoint > 0:
            self.stages.append([x0, self.yieldpoint])
            self.stages.append([self.yieldpoint, self.finalpoint])
        else:
            self.stages.append([x0, self.finalpoint])

        self.getbreakpointopti(
            nparr_x_y,
            self.initialpoint,
            self.keypoints[0][1],
            self.droppairs)
        if self.breakpoint != self.WRONGVALUE:
            if nparr_torque[self.breakpoint] > 70:
                self.breakpoint = self.WRONGVALUE

        self.linearpoints1 = []
        for v in self.stages:
            for x in range(v[0], v[1] + 1):
                self.linearpoints1.append(x)
        self.s1end = self.yieldpoint
        self.s2start = self.yieldpoint


##########################################################################

class WorkingDoggy(KeyPointGetter):

    def __init__(self):

        super(WorkingDoggy, self).__init__()

    def getmark(self):

        pass

    def getkeypoints(self):

        pass

    def getfinnalresults(self):

        pass

    def plotfinnalresults(self):

        pass

    def savefinnalresultspic(self):

        pass
