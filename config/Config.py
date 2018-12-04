# coding:utf-8
import torch
import torch.nn as nn
import numpy as np
from torch.autograd import Variable
import torch.optim as optim
import os
import time
import datetime
import ctypes
import json


class Config(object):
    r'''
    use ctypes to call C functions from python and set essential parameters.
    '''

    def __init__(self):
        base_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../release/Base.so'))
        self.lib = ctypes.cdll.LoadLibrary(base_file)
        self.lib.sampling.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.c_int64, ctypes.c_int64,
                                      ctypes.c_int64]
        self.lib.getHeadBatch.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.getTailBatch.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.testHead.argtypes = [ctypes.c_void_p]
        self.lib.testTail.argtypes = [ctypes.c_void_p]
        self.lib.getTestBatch.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.getValidBatch.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                           ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.getBestThreshold.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.test_triple_classification.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                                        ctypes.c_void_p]
        self.test_flag = False
        self.in_path = "./"
        self.out_path = "./"
        self.bern = 0
        self.hidden_size = 100
        self.ent_size = self.hidden_size
        self.rel_size = self.hidden_size
        self.train_times = 0
        self.margin = 1.0
        self.nbatches = 100
        self.negative_ent = 1
        self.negative_rel = 0
        self.workThreads = 1
        self.alpha = 0.001
        self.lmbda = 0.000
        self.log_on = 1
        self.lr_decay = 0.000
        self.weight_decay = 0.000
        self.exportName = None
        self.importName = None
        self.export_steps = 0
        self.opt_method = "SGD"
        self.optimizer = None
        self.test_link_prediction = False
        self.test_triple_classification = False

    def init_link_prediction(self):
        r'''
        import essential files and set essential interfaces for link prediction
        '''
        self.lib.importTestFiles()
        self.lib.importTypeFiles()
        self.test_h = np.zeros(self.lib.getEntityTotal(), dtype=np.int64)
        self.test_t = np.zeros(self.lib.getEntityTotal(), dtype=np.int64)
        self.test_r = np.zeros(self.lib.getEntityTotal(), dtype=np.int64)
        self.test_h_addr = self.test_h.__array_interface__['data'][0]
        self.test_t_addr = self.test_t.__array_interface__['data'][0]
        self.test_r_addr = self.test_r.__array_interface__['data'][0]

    def init_triple_classification(self):
        r'''
        import essential files and set essential interfaces for triple classification
        '''
        self.lib.importTestFiles()
        self.lib.importTypeFiles()
        self.test_pos_h = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_pos_t = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_pos_r = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_neg_h = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_neg_t = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_neg_r = np.zeros(self.lib.getTestTotal(), dtype=np.int64)
        self.test_pos_h_addr = self.test_pos_h.__array_interface__['data'][0]
        self.test_pos_t_addr = self.test_pos_t.__array_interface__['data'][0]
        self.test_pos_r_addr = self.test_pos_r.__array_interface__['data'][0]
        self.test_neg_h_addr = self.test_neg_h.__array_interface__['data'][0]
        self.test_neg_t_addr = self.test_neg_t.__array_interface__['data'][0]
        self.test_neg_r_addr = self.test_neg_r.__array_interface__['data'][0]
        self.valid_pos_h = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_pos_t = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_pos_r = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_neg_h = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_neg_t = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_neg_r = np.zeros(self.lib.getValidTotal(), dtype=np.int64)
        self.valid_pos_h_addr = self.valid_pos_h.__array_interface__['data'][0]
        self.valid_pos_t_addr = self.valid_pos_t.__array_interface__['data'][0]
        self.valid_pos_r_addr = self.valid_pos_r.__array_interface__['data'][0]
        self.valid_neg_h_addr = self.valid_neg_h.__array_interface__['data'][0]
        self.valid_neg_t_addr = self.valid_neg_t.__array_interface__['data'][0]
        self.valid_neg_r_addr = self.valid_neg_r.__array_interface__['data'][0]
        self.relThresh = np.zeros(self.lib.getRelationTotal(), dtype=np.float32)
        self.relThresh_addr = self.relThresh.__array_interface__['data'][0]

    # prepare for train and test
    def init(self):
        self.trainModel = None
        if self.in_path != None:
            self.lib.setInPath(
                ctypes.create_string_buffer(self.in_path.encode(), len(self.in_path) * 2))
            self.lib.setBern(self.bern)
            self.lib.setWorkThreads(self.workThreads)
            self.lib.randReset()
            self.lib.importTrainFiles()
            self.relTotal = self.lib.getRelationTotal()
            self.entTotal = self.lib.getEntityTotal()
            self.trainTotal = self.lib.getTrainTotal()
            self.testTotal = self.lib.getTestTotal()
            self.validTotal = self.lib.getValidTotal()
            self.batch_size = int(self.lib.getTrainTotal() / self.nbatches)
            self.batch_seq_size = self.batch_size * (1 + self.negative_ent + self.negative_rel)
            self.batch_h = np.zeros(self.batch_size * (1 + self.negative_ent + self.negative_rel),
                                    dtype=np.int64)
            self.batch_t = np.zeros(self.batch_size * (1 + self.negative_ent + self.negative_rel),
                                    dtype=np.int64)
            self.batch_r = np.zeros(self.batch_size * (1 + self.negative_ent + self.negative_rel),
                                    dtype=np.int64)
            self.batch_y = np.zeros(self.batch_size * (1 + self.negative_ent + self.negative_rel),
                                    dtype=np.float32)
            self.batch_h_addr = self.batch_h.__array_interface__['data'][0]
            self.batch_t_addr = self.batch_t.__array_interface__['data'][0]
            self.batch_r_addr = self.batch_r.__array_interface__['data'][0]
            self.batch_y_addr = self.batch_y.__array_interface__['data'][0]
        if self.test_link_prediction:
            self.init_link_prediction()
        if self.test_triple_classification:
            self.init_triple_classification()

    def get_ent_total(self):
        return self.entTotal

    def get_rel_total(self):
        return self.relTotal

    def set_lmbda(self, lmbda):
        self.lmbda = lmbda

    def set_optimizer(self, optimizer):
        self.optimizer = optimizer

    def set_opt_method(self, method):
        self.opt_method = method

    def set_test_link_prediction(self, flag):
        self.test_link_prediction = flag

    def set_test_triple_classification(self, flag):
        self.test_triple_classification = flag

    def set_log_on(self, flag):
        self.log_on = flag

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_in_path(self, path):
        self.in_path = path

    def set_out_files(self, path):
        self.out_path = path

    def set_bern(self, bern):
        self.bern = bern

    def set_dimension(self, dim):
        self.hidden_size = dim
        self.ent_size = dim
        self.rel_size = dim

    def set_ent_dimension(self, dim):
        self.ent_size = dim

    def set_rel_dimension(self, dim):
        self.rel_size = dim

    def set_train_times(self, times):
        self.train_times = times

    def set_nbatches(self, nbatches):
        self.nbatches = nbatches

    def set_margin(self, margin):
        self.margin = margin

    def set_work_threads(self, threads):
        self.workThreads = threads

    def set_ent_neg_rate(self, rate):
        self.negative_ent = rate

    def set_rel_neg_rate(self, rate):
        self.negative_rel = rate

    def set_import_files(self, path):
        self.importName = path

    def set_export_files(self, path):
        self.exportName = path

    def set_export_steps(self, steps):
        self.export_steps = steps

    def set_lr_decay(self, lr_decay):
        self.lr_decay = lr_decay

    def set_weight_decay(self, weight_decay):
        self.weight_decay = weight_decay

    # call c function for sampling
    def sampling(self):
        self.lib.sampling(self.batch_h_addr, self.batch_t_addr, self.batch_r_addr,
                          self.batch_y_addr, self.batch_size, self.negative_ent, self.negative_rel)

    # save model
    def save_pytorch(self):
        torch.save(self.trainModel.state_dict(), self.exportName)

    # restore model
    def restore_pytorch(self):
        self.trainModel.load_state_dict(torch.load(self.importName))

    # save model
    def export_variables(self, path=None):
        if path == None:
            torch.save(self.trainModel.state_dict(), self.exportName)
        else:
            torch.save(self.trainModel.state_dict(), path)

    def import_variables(self, path=None):
        if path == None:
            self.trainModel.load_state_dict(torch.load(self.importName))
        else:
            self.trainModel.load_state_dict(torch.load(path))

    def get_parameter_lists(self):
        return self.trainModel.cpu().state_dict()

    def get_parameters_by_name(self, var_name):
        return self.trainModel.cpu().state_dict().get(var_name)

    # return dict of parameters
    # parameter_name -> parameters
    def get_parameters(self, mode="numpy"):
        res = {}
        lists = self.get_parameter_lists()
        for var_name in lists:
            if mode == "numpy":
                res[var_name] = lists[var_name].numpy()
            if mode == "list":
                res[var_name] = lists[var_name].numpy().tolist()
            else:
                res[var_name] = lists[var_name]
        return res

    def save_parameters(self, path=None):
        if path == None:
            path = self.out_path
        f = open(path, "w")
        f.write(json.dumps(self.get_parameters("list")))
        f.close()

    def set_parameters_by_name(self, var_name, tensor):
        self.trainModel.state_dict().get(var_name).copy_(torch.from_numpy(np.array(tensor)))

    def set_parameters(self, lists):
        for i in lists:
            self.set_parameters_by_name(i, lists[i])

    def set_model(self, model):
        self.model = model
        self.trainModel = self.model(config=self)
        self.trainModel.cuda()
        if self.optimizer != None:
            pass
        elif self.opt_method == "Adagrad" or self.opt_method == "adagrad":
            self.optimizer = optim.Adagrad(self.trainModel.parameters(), lr=self.alpha,
                                           lr_decay=self.lr_decay, weight_decay=self.weight_decay)
        elif self.opt_method == "Adadelta" or self.opt_method == "adadelta":
            self.optimizer = optim.Adadelta(self.trainModel.parameters(), lr=self.alpha)
        elif self.opt_method == "Adam" or self.opt_method == "adam":
            self.optimizer = optim.Adam(self.trainModel.parameters(), lr=self.alpha)
        else:
            self.optimizer = optim.SGD(self.trainModel.parameters(), lr=self.alpha)

    def run(self):
        if self.importName != None:
            self.restore_pytorch()
        for epoch in range(self.train_times):
            res = 0.0
            for batch in range(self.nbatches):
                self.sampling()
                self.optimizer.zero_grad()
                loss = self.trainModel()
                res = res + loss.data[0]
                loss.backward()
                self.optimizer.step()
            if self.exportName != None and (
                    self.export_steps != 0 and epoch % self.export_steps == 0):
                self.save_pytorch()
            if self.log_on == 1:
                print(epoch)
                print(res)
        if self.exportName != None:
            self.save_pytorch()
        if self.out_path != None:
            self.save_parameters(self.out_path)

    def test(self):
        if self.importName != None:
            self.restore_pytorch()
        if self.test_link_prediction:
            total = self.lib.getTestTotal()
            for epoch in range(total):
                self.lib.getHeadBatch(self.test_h_addr, self.test_t_addr, self.test_r_addr)
                res = self.trainModel.predict(self.test_h, self.test_t, self.test_r)
                self.lib.testHead(res.data.numpy().__array_interface__['data'][0])

                self.lib.getTailBatch(self.test_h_addr, self.test_t_addr, self.test_r_addr)
                res = self.trainModel.predict(self.test_h, self.test_t, self.test_r)
                self.lib.testTail(res.data.numpy().__array_interface__['data'][0])
                if self.log_on:
                    print(epoch)
            self.lib.test_link_prediction()
        if self.test_triple_classification:
            self.lib.getValidBatch(self.valid_pos_h_addr, self.valid_pos_t_addr,
                                   self.valid_pos_r_addr, self.valid_neg_h_addr,
                                   self.valid_neg_t_addr, self.valid_neg_r_addr)
            res_pos = self.trainModel.predict(self.valid_pos_h, self.valid_pos_t, self.valid_pos_r)
            res_neg = self.trainModel.predict(self.valid_neg_h, self.valid_neg_t, self.valid_neg_r)
            self.lib.getBestThreshold(self.relThresh_addr,
                                      res_pos.data.numpy().__array_interface__['data'][0],
                                      res_neg.data.numpy().__array_interface__['data'][0])
            self.lib.getTestBatch(self.test_pos_h_addr, self.test_pos_t_addr, self.test_pos_r_addr,
                                  self.test_neg_h_addr, self.test_neg_t_addr, self.test_neg_r_addr)

            res_pos = self.trainModel.predict(self.test_pos_h, self.test_pos_t, self.test_pos_r)
            res_neg = self.trainModel.predict(self.test_neg_h, self.test_neg_t, self.test_neg_r)
            self.lib.test_triple_classification(self.relThresh_addr,
                                                res_pos.data.numpy().__array_interface__['data'][0],
                                                res_neg.data.numpy().__array_interface__['data'][0])

    def predict_head_entity(self, t, r, k):
        r'''This mothod predicts the top k head entities given tail entity and relation.

        Args:
            t (int): tail entity id
            r (int): relation id
            k (int): top k head entities

        Returns:
            list: k possible head entity ids
        '''
        self.init_link_prediction()
        if self.importName != None:
            self.restore_pytorch()
        test_h = np.array(range(self.entTotal))
        test_r = np.array([r] * self.entTotal)
        test_t = np.array([t] * self.entTotal)
        res = self.trainModel.predict(test_h, test_t, test_r).data.numpy().reshape(-1).argsort()[:k]
        print(res)
        return res

    def predict_tail_entity(self, h, r, k):
        r'''This method predicts the tail entities given head entity and relation.

        Args：
            h (int): head entity id
            r (int): relation id
            k (int): top k tail entities

        Returns:
            list: k possible tail entity ids
        '''
        self.init_link_prediction()
        if self.importName != None:
            self.restore_pytorch()
        test_h = np.array([h] * self.entTotal)
        test_r = np.array([r] * self.entTotal)
        test_t = np.array(range(self.entTotal))
        res = self.trainModel.predict(test_h, test_t, test_r).data.numpy().reshape(-1).argsort()[:k]
        print(res)
        return res

    def predict_relation(self, h, t, k):
        r'''This methods predict the relation id given head entity and tail entity.

        Args:
            h (int): head entity id
            t (int): tail entity id
            k (int): top k relations

        Returns:
            list: k possible relation ids
        '''
        self.init_link_prediction()
        if self.importName != None:
            self.restore_pytorch()
        test_h = np.array([h] * self.relTotal)
        test_r = np.array(range(self.relTotal))
        test_t = np.array([t] * self.relTotal)
        res = self.trainModel.predict(test_h, test_t, test_r).data.numpy().reshape(-1).argsort()[:k]
        print(res)
        return res

    def predict_triple(self, h, t, r, thresh=None):
        r'''This method tells you whether the given triple (h, t, r) is correct of wrong

        Args:
            h (int): head entity id
            t (int): tail entity id
            r (int): relation id
            thresh (fload): threshold for the triple
        '''
        self.init_triple_classification()
        if self.importName != None:
            self.restore_pytorch()
        res = self.trainModel.predict(np.array([h]), np.array([t]), np.array([r])).data.numpy()
        if thresh != None:
            if res < thresh:
                print("triple (%d,%d,%d) is correct" % (h, t, r))
            else:
                print("triple (%d,%d,%d) is wrong" % (h, t, r))
            return
        self.lib.getValidBatch(self.valid_pos_h_addr, self.valid_pos_t_addr, self.valid_pos_r_addr,
                               self.valid_neg_h_addr, self.valid_neg_t_addr, self.valid_neg_r_addr)
        res_pos = self.trainModel.predict(self.valid_pos_h, self.valid_pos_t, self.valid_pos_r)
        res_neg = self.trainModel.predict(self.valid_neg_h, self.valid_neg_t, self.valid_neg_r)
        self.lib.getBestThreshold(self.relThresh_addr,
                                  res_pos.data.numpy().__array_interface__['data'][0],
                                  res_neg.data.numpy().__array_interface__['data'][0])
        if res < self.relThresh[r]:
            print("triple (%d,%d,%d) is correct" % (h, t, r))
        else:
            print("triple (%d,%d,%d) is wrong" % (h, t, r))
