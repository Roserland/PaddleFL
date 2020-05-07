#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This module test fc op.

"""
import unittest
from multiprocessing import Manager

import numpy as np
import paddle.fluid as fluid
import paddle_fl.mpc as pfl_mpc
import paddle_fl.mpc.data_utils.aby3 as aby3

import test_op_base


class TestOpFC(test_op_base.TestOpBase):

    def fc(self, **kwargs):
        """
        Normal case.
        :param kwargs:
        :return:
        """
        role = kwargs['role']
        d_1 = kwargs['data_1'][role]
        return_results = kwargs['return_results']

        pfl_mpc.init("aby3", role, "localhost", self.server, int(self.port))
        data_1 = pfl_mpc.data(name='data_1', shape=[3, 2], dtype='int64')
        fc_out = pfl_mpc.layers.fc(input=data_1,
                                      size=1,
                                      param_attr=fluid.ParamAttr(
                                          initializer=fluid.initializer.ConstantInitializer(0)))
        exe = fluid.Executor(place=fluid.CPUPlace())
        exe.run(fluid.default_startup_program())
        results = exe.run(feed={'data_1': d_1}, fetch_list=[fc_out])

        self.assertEqual(results[0].shape, (2, 3, 1))
        return_results.append(results[0])

    def test_fc(self):
        data_1 = np.arange(0, 6).reshape((3, 2))
        data_1_shares = aby3.make_shares(data_1)
        data_1_all3shares = np.array([aby3.get_aby3_shares(data_1_shares, i) for i in range(3)])

        return_results = Manager().list()
        ret = self.multi_party_run(target=self.fc,
                                   data_1=data_1_all3shares,
                                   return_results=return_results)
        self.assertEqual(ret[0], True)
        revealed = aby3.reconstruct(np.array(return_results))
        expected_out = np.array([[0], [0], [0]])
        self.assertTrue(np.allclose(revealed, expected_out, atol=1e-4))


if __name__ == '__main__':
    unittest.main()
