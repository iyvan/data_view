# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 23:06:30 2016

@author: temp01
"""

import numpy as np
from pandas import DataFrame as dfm
from projectdefaults import RootInit
from stats.static import StaticDescribe
from stats.linear_regression import ols_output


class DataSorting(RootInit):
    """
    整理数据格式类，将数据整理成特定的数据库存储格式（﻿螺栓特征点数据表），供前端页面展示时取用，
    """
    def __init__(self):

        self.sd = StaticDescribe()
        # super(DataSorting,self).__init__()

    def GraphKeyPointStyle(self, df, kpobject,
                           p_id, finaltime, stages=2, clean=False):
        """
        将数据整理成特定的数据库存储格式（﻿螺栓特征点数据表），供前端页面展示时取用
        :param df:dataframe格式的扭矩转角数据
        :param kpobject:螺栓数据处理类实例（清洗和特征提取）
        :param p_id:螺栓名称
        :param finaltime:最终时间
        :param stages:分段拧紧的段数
        :param clean:暂未使用
        :return:
        """
        nparr_torque = df.torque.values
        nparr_angle = df.angle.values
        start = kpobject.initialpoint
        end = kpobject.finalpoint
        breakpoint = kpobject.breakpoint
        yieldpoint = kpobject.yieldpoint
        s1end = kpobject.s1end
        s2start = kpobject.s2start
        lrres1 = ols_output(nparr_angle[kpobject.linearpoints1],
                            nparr_torque[kpobject.linearpoints1])
        if stages > 1:
            lrres2 = ols_output(nparr_angle[kpobject.linearpoints2],
                                nparr_torque[kpobject.linearpoints2])
        else:
            lrres2 = -1.0
        MaxTorque = np.max(nparr_torque[start:end + 1])
        MAXAngle = nparr_angle[end] - nparr_angle[start]
        FINALTIME = finaltime
        StartTorque = nparr_torque[start]
        StartAngle = nparr_angle[start]
        if breakpoint > 0:
            FirstStartTor = nparr_torque[breakpoint]
            FirstStartAng = nparr_angle[breakpoint]
        else:
            FirstStartTor = nparr_torque[start]
            FirstStartAng = nparr_angle[start]
        if stages > 1:
            FirstEndTor = nparr_torque[s1end]
            FirstEndAng = nparr_angle[s1end]
            SecondStartTor = nparr_torque[s2start]
            SecondStartAng = nparr_angle[s2start]
            SecondEndTor = nparr_torque[end]
            SecondEndAng = nparr_angle[end]
        else:
            if yieldpoint > 0:
                FirstEndTor = nparr_torque[yieldpoint]
                FirstEndAng = nparr_angle[yieldpoint]
                SecondStartTor = nparr_torque[yieldpoint]
                SecondStartAng = nparr_angle[yieldpoint]
                SecondEndTor = nparr_torque[end]
                SecondEndAng = nparr_angle[end]
            else:
                FirstEndTor = nparr_torque[end]
                FirstEndAng = nparr_angle[end]
                SecondStartTor = -1.0
                SecondStartAng = -1.0
                SecondEndTor = -1.0
                SecondEndAng = -1.0
        if yieldpoint > 0:
            YieldStartTor = nparr_torque[yieldpoint]
            YieldStartAng = nparr_angle[yieldpoint]
            AngleOffYield = nparr_angle[end] - nparr_angle[yieldpoint]
        else:
            YieldStartTor = -1.0
            YieldStartAng = -1.0
            AngleOffYield = -1.0
        FirstSlope = lrres1
        SecondSlope = lrres2
        stages = kpobject.stages

        StartTorqueLabel = 0.0
        StartAngleLabel = 0.0
        FirstStartTorLabel = 0.0
        FirstStartAngLabel = 0.0
        FirstEndTorLabel = 0.0
        FirstEndAngLabel = 0.0
        SecondStartTorLabel = 0.0
        SecondStartAngLabel = 0.0
        SecondEndTorLabel = 0.0
        SecondEndAngLabel = 0.0
        YieldStartTorLabel = 0.0
        YieldStartAngLabel = 0.0
        FirstSlopeLabel = 0.0
        SecondSlopeLabel = 0.0
        AngOffYieldeLabel = 0.0

        return [p_id, MaxTorque, MAXAngle, FINALTIME, StartTorque, StartAngle,
                FirstStartTor, FirstStartAng, FirstEndTor, FirstEndAng,
                SecondStartTor, SecondStartAng, SecondEndTor, SecondEndAng,
                YieldStartTor, YieldStartAng, FirstSlope, SecondSlope,
                AngleOffYield, StartTorqueLabel, StartAngleLabel,
                FirstStartTorLabel, FirstStartAngLabel, FirstEndTorLabel,
                FirstEndAngLabel, SecondStartTorLabel, SecondStartAngLabel,
                SecondEndTorLabel, SecondEndAngLabel, YieldStartTorLabel,
                YieldStartAngLabel, FirstSlopeLabel, SecondSlopeLabel,
                AngOffYieldeLabel], [p_id, stages]
    #未使用
    def UnitsStatDesc(self, df_keypointvalues, columns, bycolumn, name, year):
        """
        按照天，月，季度等方式统计
        :param df_keypointvalues:dataframe格式的特征值（斜率，拧紧阶段起始点等）数据
        :param columns:需要统计的列名称
        :param bycolumn:按照什么进行统计（月，日，季度等）
        :param name:螺栓名称
        :param year:年份
        :return:统计结果
        """
        res = []
        header = [name, year, None, None, None]
        if bycolumn == 'date':
            index = 4
        elif bycolumn == 'month':
            header = [name, year, u'month', None, None]
            index = 3
        elif bycolumn == 'quarter':
            header = [name, year, u'quarter', None, None]
            index = 3
        else:
            raise Exception('bycolumn not defined!')
        gp = df_keypointvalues[[bycolumn] + columns].groupby(by=bycolumn)
        for v in gp:
            print v[0]
            header[index] = v[0]
            tmp = []
            for col in v[1].columns[1:]:
                descres = self.sd.describe(v[1][col])
                tmp.extend(descres)
            res.append(header + tmp)
        return res

    def UnitsStatsDescShow(
            self,
            UnitsStatStyleLeftRes,
            roundindex=2,
            mini=0.001):
        """
        将统计数据进行精确度对齐（保留相同的有效数字数）
        :param UnitsStatStyleLeftRes: 需要对齐的统计结果
        :param roundindex:需要保留的小数位数
        :param mini:用来修正的小数字
        :return:
        """
        df = dfm(UnitsStatStyleLeftRes)
        col = [x for x in range(5, 161)]
        newcol = [x + 156 for x in col]
        df[newcol] = df[col].applymap(lambda x: round(x + mini, roundindex))
