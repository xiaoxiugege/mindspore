# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
import numpy as np

import mindspore.context as context
import mindspore.nn as nn
from mindspore import Tensor
from mindspore.common.api import ms_function
from mindspore.ops import operations as P
from mindspore.ops.composite import GradOperation

context.set_context(device_target="Ascend")


class Grad(nn.Cell):
    def __init__(self, network):
        super(Grad, self).__init__()
        self.grad = GradOperation(name="get_all", get_all=True, sens_param=True)
        self.network = network

    @ms_function
    def construct(self, input, output_grad):
        return self.grad(self.network)(input, output_grad)


class Net(nn.Cell):
    def __init__(self):
        super(Net, self).__init__()
        self.maxpool = P.MaxPool(padding="SAME", ksize=3, strides=2)

    @ms_function
    def construct(self, x):
        output = self.maxpool(x)
        return output


def test_net():
    x = np.random.randn(32, 64, 112, 112).astype(np.float32)
    output_grad = np.random.randn(32, 64, 56, 56).astype(np.float32)
    net = Grad(Net())
    output = net(Tensor(x), Tensor(output_grad))
    if isinstance(output, (tuple, list)):
        output = output[0]
    print(output.asnumpy())
