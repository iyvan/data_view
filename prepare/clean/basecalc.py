# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 22:40:44 2016

@author: temp01
"""
import numpy as np
from projectdefaults import RootInit


class BaseCalc(RootInit):
    """
    定义清洗数据过程中需要用到的基础算法
    """
    def __init__(self):

        super(BaseCalc, self).__init__()

    def calcdiff(self, nparray, addvalue=0):
        """
            计算相邻数据的差值
        """

        diff = nparray[1:] - nparray[:-1]
        if addvalue != 0:
            addvalue = diff[:addvalue].mean()
        diff = diff.tolist()
        diff.insert(0, addvalue)
        return np.array(diff)

    def calcdiffdiff(self, nparray, addvalue=0):
        """
            计算相邻数据的差值的差值(差值的变化)
        """
        return self.calcdiff(
            self.calcdiff(
                nparray,
                addvalue=addvalue),
            addvalue=addvalue)

    def calcslope(self, nparr_torque, nparr_angle, start, end):
        """
            计算两点之间的斜率
        """
        return 1.0 * (nparr_torque[end] - nparr_torque[start]
                      ) / (nparr_angle[end] - nparr_angle[start])

    def calcxl(self, srsx, srsy, add=5):
        """
            计算二维数据相邻两点的斜率
        """

        diffx = srsx[1:].values - srsx[:-1].values
        diffy = srsy[1:].values - srsy[:-1].values
        if add != 0:
            addx = diffx[:add].mean()
            addy = diffy[:add].mean()
        diffx = diffx.tolist()
        diffy = diffy.tolist()
        diffx.insert(0, addx)
        diffy.insert(0, addy)
        res = np.array(diffy, dtype=np.float16) / \
            np.array(diffx, dtype=np.float16)
        res[np.isinf(res)] = 0.0
        return res

    def calcdistance(self, nparrayx, nparrayy, addx=5, addy=5):
        """
            计算二维数据相邻两点的距离
        """

        diffx = nparrayx[1:] - nparrayx[:-1]
        diffy = nparrayy[1:] - nparrayy[:-1]
        if addx != 0:
            addx = diffx[:addx].mean()
        if addy != 0:
            addy = diffy[:addy].mean()
        diffx = diffx.tolist()
        diffy = diffy.tolist()
        diffx.insert(0, addx)
        diffy.insert(0, addy)
        diffx = np.array(diffx, dtype=np.float16)
        diffy = np.array(diffy, dtype=np.float16)
        return np.sqrt(diffx * diffx + diffy * diffy)

    def calc_point_2_line(self, matrix_point, vector):
        """
            计算点到直线的距离

        """
        vector = np.array([vector])
        innerproduct = matrix_point - \
            np.dot(matrix_point, vector.T) * \
            vector * 1.0 / vector.dot(vector.T)
        return np.sqrt(innerproduct.dot(innerproduct.T).diagonal())

    def calc_angle_of_3points(
            self,
            nparr_start_x_y,
            nparr_breakpoint_x_y,
            nparr_end_x_y,
            cosmax=None,
            cosmin=None):
        """
            计算三点组成的三角形中,中间点的夹角的余弦


        """
        a = np.linalg.norm(nparr_end_x_y - nparr_start_x_y)
        b = np.linalg.norm(nparr_end_x_y - nparr_breakpoint_x_y)
        c = np.linalg.norm(nparr_breakpoint_x_y - nparr_start_x_y)
        self.cosa = (b**2 + c**2 - a**2) * 1.0 / (2 * b * c)

        return self.cosa

        # return cosmin<=cosa<=cosmax
