# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 15:55:35 2022

@author: Matteo
"""

import numpy as np
import utils
import scipy.special 

def logpdf_GAU_ND(x, mu, C):
    return -(x.shape[0]/2)*np.log(2*np.pi)-(0.5)*(np.linalg.slogdet(C)[1])- (0.5)*np.multiply((np.dot((x-mu).T, np.linalg.inv(C))).T,(x-mu)).sum(axis=0)

def logpdf_GMM(X, gmm):
    S = np.zeros((len(gmm), X.shape[1]))
    for i in range(len(gmm)):
        # Compute log density
        S[i, :] = logpdf_GAU_ND(X, gmm[i][1], gmm[i][2])
    return S

def joint_log_density_GMM (S, gmm):
    
    for i in range(len(gmm)):
        # Add log of the prior of the corresponding component
        S[i, :] += np.log(gmm[i][0])
    return S

def marginal_density_GMM (S):
    return scipy.special.logsumexp(S, axis = 0)


def log_likelihood_GMM(logmarg, X):
    return np.sum(logmarg)/X.shape[1]

def compute_posterior_GMM(X, gmm):
     return marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm),gmm))






def Estep(logdens, S):
    # E-step: compute the POSTERIOR PROBABILITY (=responsibilities) for each component of the GMM
    # for each sample, using the previous estimate of the model parameters.
    return np.exp(S-logdens.reshape(1, logdens.size))


def Mstep(X, S, posterior):
    Zg = np.sum(posterior, axis=1)  # 3
    Fg = np.zeros((X.shape[0], S.shape[0]))  # 4x3
    for g in range(S.shape[0]):
        tempSum = np.zeros(X.shape[0])
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * X[:, i]
        Fg[:, g] = tempSum
    Sg = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        tempSum = np.zeros((X.shape[0], X.shape[0]))
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * np.dot(X[:, i].reshape(
                (X.shape[0], 1)), X[:, i].reshape((1, X.shape[0])))
        Sg[g] = tempSum
    mu = Fg / Zg
    prodmu = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        prodmu[g] = np.dot(mu[:, g].reshape((X.shape[0], 1)),
                           mu[:, g].reshape((1, X.shape[0])))
    cov = Sg / Zg.reshape((Zg.size, 1, 1)) - prodmu
    for g in range(S.shape[0]):        
        cov[g] = utils.constrainCov(cov[g])
    w = Zg/np.sum(Zg)
    return (w, mu, cov)

def DiagMstep(X, S, posterior):
    Zg = np.sum(posterior, axis=1)  # 3
    Fg = np.zeros((X.shape[0], S.shape[0]))  # 4x3
    for g in range(S.shape[0]):
        tempSum = np.zeros(X.shape[0])
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * X[:, i]
        Fg[:, g] = tempSum
    Sg = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        tempSum = np.zeros((X.shape[0], X.shape[0]))
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * np.dot(X[:, i].reshape(
                (X.shape[0], 1)), X[:, i].reshape((1, X.shape[0])))
        Sg[g] = tempSum
    mu = Fg / Zg
    prodmu = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        prodmu[g] = np.dot(mu[:, g].reshape((X.shape[0], 1)),
                           mu[:, g].reshape((1, X.shape[0])))
    cov = Sg / Zg.reshape((Zg.size, 1, 1)) - prodmu
    for g in range(S.shape[0]):
       
        cov[g] = utils.constrainSigma(cov[g] * np.eye(cov[g].shape[0]))
    w = Zg/np.sum(Zg)
    return (w, mu, cov)


def TiedMstep(X, S, posterior):
    Zg = np.sum(posterior, axis=1)  
    Fg = np.zeros((X.shape[0], S.shape[0])) 
    for g in range(S.shape[0]):
        tempSum = np.zeros(X.shape[0])
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * X[:, i]
        Fg[:, g] = tempSum
    Sg = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        tempSum = np.zeros((X.shape[0], X.shape[0]))
        for i in range(X.shape[1]):
            tempSum += posterior[g, i] * np.dot(X[:, i].reshape(
                (X.shape[0], 1)), X[:, i].reshape((1, X.shape[0])))
        Sg[g] = tempSum
    mu = Fg / Zg
    prodmu = np.zeros((S.shape[0], X.shape[0], X.shape[0]))
    for g in range(S.shape[0]):
        prodmu[g] = np.dot(mu[:, g].reshape((X.shape[0], 1)),
                           mu[:, g].reshape((1, X.shape[0])))
    cov = Sg / Zg.reshape((Zg.size, 1, 1)) - prodmu
    tsum = np.zeros((cov.shape[1], cov.shape[2]))
    for g in range(S.shape[0]):
        tsum += Zg[g]*cov[g]
    for g in range(S.shape[0]):
        cov[g] = utils.constrainCov(1/X.shape[1] * tsum)
    w = Zg/np.sum(Zg)
    return (w, mu, cov)

def EMalgorithm(X, gmm, delta=10**(-6)):
    flag = True
    while(flag):
        # Given the training set and the initial model parameters, compute
        # log marginal densities and sub-class conditional densities
        S = joint_log_density_GMM(logpdf_GMM(X, gmm), gmm)
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )                                    
        # Compute the AVERAGE loglikelihood, by summing all the log densities and
        # dividing by the number of samples (it's as if we're computing a mean)
        loglikelihood1 = log_likelihood_GMM(logmarg, X)
        # ------ E-step ----------
        posterior = Estep(logmarg, S)
        # ------ M-step ----------
        (w, mu, cov) = Mstep(X, S, posterior)
        for g in range(len(gmm)):
            # Update the model parameters that are in gmm
            gmm[g] = (w[g], mu[:, g].reshape((mu.shape[0], 1)), cov[g])
        # Compute the new log densities and the new sub-class conditional densities
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )                                                                            #aggiustare
        loglikelihood2 = log_likelihood_GMM(logmarg, X)
        if (loglikelihood2-loglikelihood1 < delta):
            flag = False
        if (loglikelihood2-loglikelihood1 < 0):
            print("ERROR, LOG-LIKELIHOOD IS NOT INCREASING")
    return gmm

def DiagEMalgorithm(X, gmm, delta=10**(-6)):
    flag = True
    while(flag):
        # Given the training set and the initial model parameters, compute
        # log marginal densities and sub-class conditional densities
        S = joint_log_density_GMM(logpdf_GMM(X, gmm), gmm)
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )
        # Compute the AVERAGE loglikelihood, by summing all the log densities and
        # dividing by the number of samples (it's as if we're computing a mean)
        loglikelihood1 = log_likelihood_GMM(logmarg, X)
        # ------ E-step ----------
        posterior = Estep(logmarg, S)
        # ------ M-step ----------
        (w, mu, cov) = DiagMstep(X, S, posterior)
        for g in range(len(gmm)):
            # Update the model parameters that are in gmm
            gmm[g] = (w[g], mu[:, g].reshape((mu.shape[0], 1)), cov[g])
        # Compute the new log densities and the new sub-class conditional densities
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )                                                                            #aggiustare
        loglikelihood2 = log_likelihood_GMM(logmarg, X)
        if (loglikelihood2-loglikelihood1 < delta):
            flag = False
        if (loglikelihood2-loglikelihood1 < 0):
            print("ERROR, LOG-LIKELIHOOD IS NOT INCREASING")
    return gmm


def TiedEMalgorithm(X, gmm, delta=10**(-6)):
    flag = True
    while(flag):
        # Given the training set and the initial model parameters, compute
        # log marginal densities and sub-class conditional densities
        S = joint_log_density_GMM(logpdf_GMM(X, gmm), gmm)
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )
        # Compute the AVERAGE loglikelihood, by summing all the log densities and
        # dividing by the number of samples (it's as if we're computing a mean)
        loglikelihood1 = log_likelihood_GMM(logmarg, X)
        # ------ E-step ----------
        posterior = Estep(logmarg, S)
        # ------ M-step ----------
        (w, mu, cov) = TiedMstep(X, S, posterior)
        for g in range(len(gmm)):
            # Update the model parameters that are in gmm
            gmm[g] = (w[g], mu[:, g].reshape((mu.shape[0], 1)), cov[g])
        # Compute the new log densities and the new sub-class conditional densities
        logmarg= marginal_density_GMM(joint_log_density_GMM(logpdf_GMM(X, gmm), gmm) )                                                                            #aggiustare
        loglikelihood2 = log_likelihood_GMM(logmarg, X)
        if (loglikelihood2-loglikelihood1 < delta):
            flag = False
        if (loglikelihood2-loglikelihood1 < 0):
            print("ERROR, LOG-LIKELIHOOD IS NOT INCREASING")
    return gmm