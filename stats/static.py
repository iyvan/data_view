#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
均值,df.mean()
标准差,df.std()
极差,df.max() - df.min()
变异系数,df.std()/df.mean()
众数,mode(df)[0]
算术中位数,df.median()
偏度,df.skew()
峰度,df.kurt()
p分位数,df.quantile(p)
一个标准差样本覆盖率,
二个标准差样本覆盖率,
三个标准差样本覆盖率,
'''
import pandas as pd
import numpy as np
#from pandas import Series as srs
from scipy.stats import mode
from math import ceil
import sys
sys.setrecursionlimit(1000000)

# 基本描述统计量


class StaticDescribe(object):
    """
    对提取的特征点及斜率进行统计
    """
    def __init__(self):
        self.label = ['mean', 'median', 'Mode', 'Range', 'skew',
                      'kurt', 'firstquarter', 'thirdquarter',
                      'std', 'cv', 'covers1', 'covers2', 'covers3'
                      ]

    def describe(self, npsrs, percentiles=[0.25, 0.75]):
        """
        进行统计
        :param npsrs: series 格式的数据
        :param percentiles: 分位数
        :return: 统计结果，服务于前端展示的统计图右边的指标
        """
        nparr = npsrs.values
        nparrmode = map(lambda x: round(x + 0.0001, 2), nparr)
        mean = npsrs.mean()
        std = npsrs.std()
        Range = npsrs.max() - npsrs.min()
        cv = std * 1.0 / mean
        median = npsrs.median()
        skew = npsrs.skew()
        kurt = npsrs.kurt()
        moder = mode(nparrmode)
        Mode = moder.mode[0]
        # modecount=moder.count[0]
        lenth = len(npsrs)
        covers1 = np.sum((mean + std > npsrs.values) &
                         (npsrs.values > mean - std)) * 1.0 / lenth
        covers2 = np.sum((mean + 2 * std > nparr) &
                         (nparr > mean - 2 * std)) * 1.0 / lenth
        covers3 = np.sum((mean + 3 * std > nparr) &
                         (nparr > mean - 3 * std)) * 1.0 / lenth
        firstq, thirdq = npsrs.quantile(percentiles)
        return [mean, median, Mode, Range, skew, kurt, firstq, thirdq,
                std, cv, covers1, covers2, covers3
                ]

    def calcdesc(self, df, columns, bycolumn, name, year):

        """
        按照天，月，季度等方式统计
        :param df:dataframe格式的特征值（斜率，拧紧阶段起始点等）数据
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
        elif bycolumn == 'week':
            header =[name, year, u'week', None, None]
            index = 3
        else:
            raise Exception('bycolumn not defined!')
        gp = df[[bycolumn] + columns].groupby(by=bycolumn)
        for v in gp:
            print v[0]
            header[index] = v[0]
            tmp = []
            for col in v[1].columns[1:]:
                descres = self.describe(v[1][col])
                tmp.extend(descres)
            res.append(header + tmp )
        return res


#未使用
def describe_nums(df, p):
    # 众数
    def zhongshu(df):
        return u'众数', mode(df).mode, mode(df).count

    # p分位数,p的值在0-1之间
    def p_cnt(df, s):
        p_cnts = []
        for i in range(s + 1):
            p_cnts.append(str(df.quantile(i * 1.0 / s)))
        return p_cnts

    # p个标准差样本覆盖率
    def p_cover(df, t):
        bs = pd.Series(map(ceil, abs((df - df.mean()) / df.std())))
        covers = bs[bs <= t].shape[0] * 1.0 / bs.shape[0]
        return covers
    state_result = pd.DataFrame()
    # 均值
    state_result['Mean'] = pd.Series(df.mean())
    # 标准差
    state_result['Std'] = pd.Series(df.std())
    # 极差
    state_result['Range'] = pd.Series(df.max() - df.min())
    # 变异系数
    state_result['CV'] = pd.Series(df.std() / df.mean())
    # 算术中位数
    state_result['median'] = pd.Series(df.median())
    # 偏度
    state_result['skew'] = pd.Series(df.skew())
    # 峰度
    state_result['kurt'] = pd.Series(df.kurt())
    # 众数以及个数
    state_result['mode'] = pd.Series(mode(df).mode)
    state_result['mode_count'] = pd.Series(mode(df).count)
    # p个标准差样本覆盖率
    state_result['covers1'] = pd.Series(p_cover(df, 1))
    state_result['covers2'] = pd.Series(p_cover(df, 2))
    #state_result['covers3'] = pd.Series(p_cover(df,3))
    # p分位数
    for i in xrange(p + 1):
        state_result['%.3fcnt' %
                     (i * 1.0 / p)] = pd.Series(p_cnt(df, p)[i])
    return state_result
