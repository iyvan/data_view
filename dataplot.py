#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 24 12:13:06 2016

@author: Forever_NIP
"""
#import gc
import seaborn
# matplotlib.use('Agg')
from matplotlib import pyplot as plt
#from matplotlib.pyplot import savefig
from matplotlib import animation
#from test.preprocessdata_new import DefaultValues
seaborn.set_style('darkgrid')


"""
数据可视化方法
"""

class PlotKeypforchk(object):
    """
    打印找到的特征点，来检查数据清洗算法是否可靠
    """
    def __init__(self, colorls=['0.85', 'g', 'r', 'b'],
                 colx='angle', coly='torque'):
        self.colorls = colorls
        self.colx = colx
        self.coly = coly

    def plotstartend(self,df,start,end):
        """
        打印数据，对数据进行线条刻画，然后打印散点
        :param df: dataframe格式的扭矩转角数据
        :param start: 需要打印的散点起始点
        :param end: 需要打印的散点终止点
        :return:
        """
        plt.plot(df.angle,df.torque,lw=0.8,c='0.8')
        plt.scatter(df.angle.values[start:end+1],df.torque.values[start:end+1],marker='.',s=8)
        plt.show()

    def plot(self, df, keypoints, droppars, yieldp=None, breakp=None):
        """
        打印数据，并将特征点，垃圾数据标明
        :param df: dataframe格式的扭矩转角数据
        :param keypoints: 特征点列表
        :param droppars: 垃圾数据对列表
        :param yieldp: 屈服点
        :param breakp: 线性变化起始点
        :return:
        """
        plt.plot(df[self.colx].values, df[self.coly].values,
                 c=self.colorls[0], lw=0.8)
        plt.plot(df[self.colx].values[[keypoints[-1][0],keypoints[-1][1]]],
                 df[self.coly].values[[keypoints[-1][0],keypoints[-1][1]]],
                  lw=0.8,c='r')
        for dp in droppars:
            plt.plot(df[self.colx].values[dp[0]:dp[1]], df[
                     self.coly].values[dp[0]:dp[1]], c='r', lw=0.8)
        for k in keypoints:
            plt.plot(df[self.colx].values[k[0]:k[1] +
                                          1], df[self.coly].values[k[0]:k[1] +
                                                                   1], c=self.colorls[1], lw=1.2)

        if yieldp is not None and yieldp != -99999999:
            plt.scatter(df[self.colx].values[yieldp], df[self.coly].values[
                        yieldp], s=50, marker='*', c=self.colorls[2])

        if breakp is not None and breakp != -99999999:
            plt.scatter(df[self.colx].values[breakp], df[self.coly].values[
                        breakp], s=50, marker='*', c=self.colorls[3])

        plt.show()


class plotdata(object):

    def __init__(self):

        self.speed = 10
        self.sample = None
        self.line = None

    def setspeed(self, speed):

        self.speed = 100 / speed

    def animate(self, i):

        x = self.sample.angle.values[:i]
        y = self.sample.torque.values[:i]
        self.line.set_data(x, y)
        self.line.set_color('red')
        return self.line

    def init(self):

        self.line.set_data([], [])
        return self.line

    def plotanimationc(self, sample):
        self.sample = sample
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.scatter(
            self.sample.angle.values,
            self.sample.torque.values,
            c='g',
            marker='.')
        self.line, = ax.plot(self.sample.angle.values,
                             self.sample.torque.values, c='0.9')

        anim1 = animation.FuncAnimation(
            fig, self.animate, init_func=self.init, frames=len(
                self.sample) - 1, interval=self.speed)
        return anim1


def plotanimationf(sample, speed=10):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(sample.angle.values, sample.torque.values, c='g', marker='.')
    line, = ax.plot(sample.angle.values, sample.torque.values, c='0.9')

    def init():
        line.set_data([], [])
        return line

    # animation function.  this is called sequentially
    def animate(i):
        x = sample.angle.values[:i]
        y = sample.torque.values[:i]
        line.set_data(x, y)
        line.set_color('red')
        return line

    anim1 = animation.FuncAnimation(
        fig,
        animate,
        init_func=init,
        frames=len(sample) - 1,
        interval=speed)
    return anim1
