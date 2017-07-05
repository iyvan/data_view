import numpy as np
import pandas as pd
import copy
import cPickle
#import stats.subbarrel as subbarrel

#def subbarrel(slope, n=20):
#    if n == -1:
#        n = int(np.sqrt(len(slope)))
#    n = np.floor(n)
#    maxv, minv = slope.max(), slope.min()
#    slope[np.isnan(slope)] = slope.mean()
#    space = (maxv - minv) / float(n)
#    result = (slope - slope.min()) / (space + 0.00001)
#    return np.modf(result)[1]
#
#
#def subbarrelv(nparr, n=20):
#    if n == -1:
#        n = int(np.sqrt(len(nparr)))
#    minv = nparr.min()
#    maxv = nparr.max()
#    bins = np.linspace(minv, maxv, n + 1)
#    labels = (bins[1:] + bins[0:-1]) / 2.0
#    res = pd.cut(nparr, bins)
#    return labels[res.labels]


class Subbar(object):

    def __init__(self, name, modelpath, percent=98):

        self.lb = None
        self.bins = None
        self.minv = None
        self.maxv = None
        self.finnalresult = None
        self.cutres = None
        self.n = None
        self.name = name
        self.percent = percent
        self.percentmin = None
        self.percentmax = None
        self.avg = None
        self.nparr = None
        self.modelpath = modelpath
        self.fitted = False

    def fit(self, nparr, n=20):

        self.percentmin = np.percentile(nparr, 100 - self.percent)
        self.percentmax = np.percentile(nparr, self.percent)
        self.avg = np.mean(nparr)
        self.n = n
        if self.n == -1:
            self.n = int(np.sqrt(len(nparr)))
        self.minv = nparr.min()
        self.maxv = nparr.max()
        self.bins = np.linspace(self.minv - 0.1, self.maxv + 0.1, n + 1)
        self.lb = (self.bins[1:] + self.bins[0:-1]) / 2.0
        self.fitted = True

    def transform(self, nparr, modelname=None):

        if not self.fitted:
            raise Exception('model must be fitted fist!')
        self.nparr = copy.deepcopy(nparr)
        self.nparr[(self.nparr < self.percentmin) | (
            self.nparr > self.percentmax)] = self.avg
        self.cutres = pd.cut(self.nparr, self.bins)
        self.finnalresult = self.lb[self.cutres.labels]
        return self.finnalresult

    def fit_transform(self, nparr, n=20):

        self.nparr = copy.deepcopy(nparr)
        self.percentmin = np.percentile(self.nparr, 100 - self.percent)
        self.percentmax = np.percentile(self.nparr, self.percent)
        self.avg = np.mean(self.nparr)
        self.nparr[(self.nparr < self.percentmin) | (
            self.nparr > self.percentmax)] = self.avg
        self.n = n
        if self.n == -1:
            self.n = int(np.sqrt(len(self.nparr)))
        self.minv = self.nparr.min()
        self.maxv = self.nparr.max()
        self.bins = np.linspace(self.minv - 0.1, self.maxv + 0.1, n + 1)
        self.lb = (self.bins[1:] + self.bins[0:-1]) / 2.0
        self.cutres = pd.cut(self.nparr, self.bins)
        self.finnalresult = self.lb[self.cutres.labels]
        self.fitted = True
        return self.finnalresult

    def freeze(self, model, modelname):

        self.nparr = None
        self.finnalresult = None
        self.cutres = None

        with open(self.modelpath + '/' + modelname + '.mdl', 'wb') as f:
            cPickle.dump(model, f)

    #@staticmethod
    def load(self,modelpath, modelname):

        with open(modelpath + '/' + modelname + '.mdl', 'rb') as f:
            model = cPickle.load(f)
        return model
