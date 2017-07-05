import numpy as np
import pandas as pd
import copy
import cPickle
from projectdefaults import RootInit


def subbarrel(slope, n=20):
    if n == -1:
        n = int(np.sqrt(len(slope)))
    n = np.floor(n)
    maxv,minv=slope.max(),slope.min()
    slope[np.isnan(slope)] = slope.mean()
    space = (maxv - minv) / float(n)
    result = (slope - slope.min()) / (space + 0.00001)
    return np.modf(result)[1]


def subbarrelv(nparr,n=20):
    if n == -1:
        n=int(np.sqrt(len(nparr)))
    minv=nparr.min()
    maxv=nparr.max()
    bins=np.linspace(minv,maxv,n+1)
    labels=(bins[1:]+bins[0:-1])/2.0
    res= pd.cut(nparr,bins )
    return labels[res.labels]


class Subbar(RootInit):
    """
    为前端展示柱状图而进行的分桶操作
    """
    def __init__(self,name,modelpath,percent=98):
        """
        :param name: 螺栓名称
        :param modelpath: 分桶模型路径
        :param percent: 分桶时参考的数据的百分比单边上限
        """
        super(Subbar,self).__init__()

        self.lb=None
        self.bins=None
        self.minv=None
        self.maxv=None
        self.finnalresult=None
        self.cutres=None
        self.n=None
        self.name=name
        self.percent=percent
        self.percentmin=None
        self.percentmax=None
        self.avg=None
        self.nparr=None
        self.modelpath=modelpath
        self.fitted=False
        
    def fit(self,nparr,n=20):
        """
        根据数据计算桶位
        :param nparr: 需要分桶的数据
        :param n: 桶的数量
        :return:
        """
        self.percentmin=np.percentile(nparr,100-self.percent)
        self.percentmax=np.percentile(nparr,self.percent)
        #self.avg=np.mean(nparr)
        self.n=n
        if self.n == -1:
            self.n=int(np.sqrt(len(nparr)))
        #self.minv=nparr.min()
        #self.maxv=nparr.max()
        #self.bins=np.linspace(self.minv-0.1,self.maxv+0.1,n+1)
        self.bins=np.linspace(self.percentmin-0.0001,self.percentmax+0.0001,n+1)
        self.lb=(self.bins[1:]+self.bins[0:-1])/2.0
        self.fitted=True
        
    def transform(self,nparr,modelname=None):
        """
        根据桶位，对数据分桶
        :param nparr: 待分桶的数据
        :param modelname:桶名称
        :return: 分桶的结果
        """
        if self.fitted==False:
            raise Exception('model must be fitted fist!')
        self.nparr=copy.deepcopy(nparr)
        self.nparr[(self.nparr<self.percentmin)|(self.nparr>self.percentmax)]=self.WRONGVALUE
        step = self.bins[1]-self.bins[0]
        if round(self.percentmax,4) > round(self.bins[-1],4)+0.0001:
            right = np.arange(self.bins[-1],self.percentmax+step,step)
            self.bins = np.append(self.bins,right[1:])
        if round(self.percentmin,4) < round(self.bins[0],4)+0.0001:
            left = np.arange(self.bins[0]-step,self.percentmin-step,-step)
            left = left[-1::-1]
            self.bins = np.insert(self.bins,0,left)
        self.cutres= pd.cut(self.nparr,self.bins )
        self.finnalresult=self.lb[self.cutres.labels]
        self.finnalresult[self.cutres.labels==-1]=self.WRONGVALUE
        return self.finnalresult
        
    def fit_transform(self,nparr,n=20):
        """
        合并上述两个方法的操作
        :param nparr: 待分桶的数据
        :param n: 桶的数量
        :return: 分桶的结果
        """
        self.nparr=copy.deepcopy(nparr)
        self.percentmin=np.percentile(self.nparr,100-self.percent)
        self.percentmax=np.percentile(self.nparr,self.percent)
        #self.avg=np.mean(self.nparr)
        self.nparr[(self.nparr<self.percentmin)|(self.nparr>self.percentmax)]=self.WRONGVALUE
        self.n=n
        if self.n == -1:
            self.n=int(np.sqrt(len(self.nparr)))
        #self.minv=self.nparr.min()
        #self.maxv=self.nparr.max()
        #self.bins=np.linspace(self.minv-0.1,self.maxv+0.1,n+1)
        self.bins=np.linspace(self.percentmin-0.0001,self.percentmax+0.0001,n+1)        
        self.lb=(self.bins[1:]+self.bins[0:-1])/2.0
        self.cutres= pd.cut(self.nparr,self.bins )
        self.finnalresult=self.lb[self.cutres.labels]
        self.finnalresult[self.cutres.labels==-1]=self.WRONGVALUE
        self.fitted=True
        return self.finnalresult
    
    def freeze(self,model,modelname):
        """
        将分桶的桶位模型保存
        :param model: 需要保存的分桶模型
        :param modelname: 模型名称
        :return:
        """
        self.nparr=None
        self.finnalresult=None
        self.cutres=None
        
        with open(self.modelpath+'/'+modelname+'.mdl','wb') as f:
            cPickle.dump(model,f)
    #@staticmethod
    def load(self,modelpath,modelname):
        """
        加载之前的桶位模型
        :param modelpath: 模型目录路径
        :param modelname: 模型名称
        :return: 分桶模型
        """
        with open(modelpath+'/'+modelname+'.mdl','rb') as f:
            model=cPickle.load(f)
        return model
    
        
        