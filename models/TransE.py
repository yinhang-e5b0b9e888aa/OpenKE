import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from .Model import Model
from torch.autograd import Variable


class TransE(Model):

    def __init__(self, config):
        super(TransE, self).__init__(config)
        self._ent_embeddings = nn.Embedding(config.entTotal, config.hidden_size)
        self._rel_embeddings = nn.Embedding(config.relTotal, config.hidden_size)
        self.init_weights()

    def init_weights(self):
        nn.init.xavier_uniform(self._ent_embeddings.weight.data)
        nn.init.xavier_uniform(self._rel_embeddings.weight.data)

    r'''
    TransE is the first model to introduce translation-based embedding, 
    which interprets relations as the translations operating on entities.
    '''

    def _calc(self, h, t, r):
        return torch.abs(h + r - t)

    # margin-based loss
    def loss_func(self, p_score, n_score):
        criterion = nn.MarginRankingLoss(self.config.margin, False).cuda()
        y = Variable(torch.Tensor([-1])).cuda()
        loss = criterion(p_score, n_score, y)
        return loss

    def forward(self):
        pos_h, pos_t, pos_r = self.get_postive_instance()
        neg_h, neg_t, neg_r = self.get_negtive_instance()
        p_h = self._ent_embeddings(pos_h)
        p_t = self._ent_embeddings(pos_t)
        p_r = self._rel_embeddings(pos_r)
        n_h = self._ent_embeddings(neg_h)
        n_t = self._ent_embeddings(neg_t)
        n_r = self._rel_embeddings(neg_r)
        _p_score = self._calc(p_h, p_t, p_r)
        _n_score = self._calc(n_h, n_t, n_r)
        _p_score = _p_score.view(-1, 1, self.config.hidden_size)
        _n_score = _n_score.view(-1, self.config.negative_ent + self.config.negative_rel,
                                 self.config.hidden_size)
        p_score = torch.sum(torch.mean(_p_score, 1), 1)
        n_score = torch.sum(torch.mean(_n_score, 1), 1)
        loss = self.loss_func(p_score, n_score)
        return loss

    def predict(self, predict_h, predict_t, predict_r):
        p_h = self._ent_embeddings(Variable(torch.from_numpy(predict_h)).cuda())
        p_t = self._ent_embeddings(Variable(torch.from_numpy(predict_t)).cuda())
        p_r = self._rel_embeddings(Variable(torch.from_numpy(predict_r)).cuda())
        _p_score = self._calc(p_h, p_t, p_r)
        p_score = torch.sum(_p_score, 1)
        return p_score.cpu()
