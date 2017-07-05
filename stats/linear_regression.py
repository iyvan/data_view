# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 22:55:25 2016

@author: BIFROST
"""

import pandas as pd
import statsmodels.api as sm
import math


def ols_output(x, y, inter=True, angle=True):
    '''
    线性回归方法
    x：自变量数据
    y：因变量数据
    inter：是否仅返回回归斜率
    angle：是否以角度为单位返回
    type of x & y ：series
    output ： rsquare, f-value of model, p-value of f-test, coef of intercept & slope
    for patameters, we have estimated value, p-value of t-test and the 95% confidence interval
    '''
    X = sm.add_constant(x)
    result = sm.OLS(y, X).fit()
    if inter and angle:
        return math.atan(result.params[1]) * 180 / math.pi
    kpi = [result.rsquared, result.fvalue, result.f_pvalue, result.params[0],
           result.summary().tables[1].data[1][4],
           result.summary().tables[1].data[1][5].split()[0],
           result.summary().tables[1].data[1][5].split()[1],
           result.params[1], result.summary().tables[1].data[2][4],
           result.summary().tables[1].data[2][5].split()[0],
           result.summary().tables[1].data[2][5].split()[1]]
    output = pd.DataFrame(kpi).T
    output.columns = [
        'rsquare',
        'F-value',
        'F-pvalue',
        'parameter_intercept',
        'parameter_pvalue_intercept',
        'perc95_conf_lower_intercept',
        'perc95_conf_upper_intercept',
        'parameter_slope',
        'parameter_pvalue_slope',
        'perc95_conf_lower_slope',
        'perc95_conf_upper_slope']
    return output
