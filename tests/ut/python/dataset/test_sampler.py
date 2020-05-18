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
# ==============================================================================
import numpy as np

import mindspore.dataset as ds
from mindspore import log as logger


# test5trainimgs.json contains 5 images whose un-decoded shape is [83554, 54214, 65512, 54214, 64631]
# the label of each image is [0,0,0,1,1] each image can be uniquely identified
# via the following lookup table (dict){(83554, 0): 0, (54214, 0): 1, (54214, 1): 2, (65512, 0): 3, (64631, 1): 4}

def test_sequential_sampler(print_res=False):
    manifest_file = "../data/dataset/testManifestData/test5trainimgs.json"
    map = {(172876, 0): 0, (54214, 0): 1, (54214, 1): 2, (173673, 0): 3, (64631, 1): 4}

    def test_config(num_samples, num_repeats=None):
        sampler = ds.SequentialSampler()
        data1 = ds.ManifestDataset(manifest_file, num_samples=num_samples, sampler=sampler)
        if num_repeats is not None:
            data1 = data1.repeat(num_repeats)
        res = []
        for item in data1.create_dict_iterator():
            logger.info("item[image].shape[0]: {}, item[label].item(): {}"
                        .format(item["image"].shape[0], item["label"].item()))
            res.append(map[(item["image"].shape[0], item["label"].item())])
        if print_res:
            logger.info("image.shapes and labels: {}".format(res))
        return res

    assert test_config(num_samples=3, num_repeats=None) == [0, 1, 2]
    assert test_config(num_samples=None, num_repeats=2) == [0, 1, 2, 3, 4] * 2
    assert test_config(num_samples=4, num_repeats=2) == [0, 1, 2, 3] * 2


def test_random_sampler(print_res=False):
    manifest_file = "../data/dataset/testManifestData/test5trainimgs.json"
    map = {(172876, 0): 0, (54214, 0): 1, (54214, 1): 2, (173673, 0): 3, (64631, 1): 4}

    def test_config(replacement, num_samples, num_repeats):
        sampler = ds.RandomSampler(replacement=replacement, num_samples=num_samples)
        data1 = ds.ManifestDataset(manifest_file, sampler=sampler)
        data1 = data1.repeat(num_repeats)
        res = []
        for item in data1.create_dict_iterator():
            res.append(map[(item["image"].shape[0], item["label"].item())])
        if print_res:
            logger.info("image.shapes and labels: {}".format(res))
        return res

    # this tests that each epoch COULD return different samples than the previous epoch
    assert len(set(test_config(replacement=False, num_samples=2, num_repeats=6))) > 2
    # the following two tests test replacement works
    ordered_res = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
    assert sorted(test_config(replacement=False, num_samples=None, num_repeats=4)) == ordered_res
    assert sorted(test_config(replacement=True, num_samples=None, num_repeats=4)) != ordered_res


def test_random_sampler_multi_iter(print_res=False):
    manifest_file = "../data/dataset/testManifestData/test5trainimgs.json"
    map = {(172876, 0): 0, (54214, 0): 1, (54214, 1): 2, (173673, 0): 3, (64631, 1): 4}

    def test_config(replacement, num_samples, num_repeats, validate):
        sampler = ds.RandomSampler(replacement=replacement, num_samples=num_samples)
        data1 = ds.ManifestDataset(manifest_file, sampler=sampler)
        while num_repeats > 0:
            res = []
            for item in data1.create_dict_iterator():
                res.append(map[(item["image"].shape[0], item["label"].item())])
            if print_res:
                logger.info("image.shapes and labels: {}".format(res))
            if validate != sorted(res):
                break
            num_repeats -= 1
        assert num_repeats > 0

    test_config(replacement=True, num_samples=5, num_repeats=5, validate=[0, 1, 2, 3, 4, 5])


def test_sampler_py_api():
    sampler = ds.SequentialSampler().create()
    sampler.set_num_rows(128)
    sampler.set_num_samples(64)
    sampler.initialize()
    sampler.get_indices()

    sampler = ds.RandomSampler().create()
    sampler.set_num_rows(128)
    sampler.set_num_samples(64)
    sampler.initialize()
    sampler.get_indices()

    sampler = ds.DistributedSampler(8, 4).create()
    sampler.set_num_rows(128)
    sampler.set_num_samples(64)
    sampler.initialize()
    sampler.get_indices()


def test_python_sampler():
    manifest_file = "../data/dataset/testManifestData/test5trainimgs.json"
    map = {(172876, 0): 0, (54214, 0): 1, (54214, 1): 2, (173673, 0): 3, (64631, 1): 4}

    class Sp1(ds.Sampler):
        def __iter__(self):
            return iter([i for i in range(self.dataset_size)])

    class Sp2(ds.Sampler):
        def __init__(self):
            super(Sp2, self).__init__()
            # at this stage, self.dataset_size and self.num_samples are not yet known
            self.cnt = 0

        def __iter__(self):  # first epoch, all 0, second epoch all 1, third all 2 etc.. ...
            return iter([self.cnt for i in range(self.num_samples)])

        def reset(self):
            self.cnt = (self.cnt + 1) % self.dataset_size

    def test_config(num_samples, num_repeats, sampler):
        data1 = ds.ManifestDataset(manifest_file, num_samples=num_samples, sampler=sampler)
        if num_repeats is not None:
            data1 = data1.repeat(num_repeats)
        res = []
        for item in data1.create_dict_iterator():
            logger.info("item[image].shape[0]: {}, item[label].item(): {}"
                        .format(item["image"].shape[0], item["label"].item()))
            res.append(map[(item["image"].shape[0], item["label"].item())])
        # print(res)
        return res

    def test_generator():
        class MySampler(ds.Sampler):
            def __iter__(self):
                for i in range(99, -1, -1):
                    yield i

        data1 = ds.GeneratorDataset([(np.array(i),) for i in range(100)], ["data"], sampler=MySampler())
        i = 99
        for data in data1:
            assert data[0] == (np.array(i),)
            i = i - 1

    assert test_config(5, 2, Sp1()) == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
    assert test_config(2, 6, Sp2()) == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0]
    test_generator()

    sp1 = Sp1().create()
    sp1.set_num_rows(5)
    sp1.set_num_samples(5)
    sp1.initialize()
    assert list(sp1.get_indices()) == [0, 1, 2, 3, 4]


if __name__ == '__main__':
    test_sequential_sampler(True)
    test_random_sampler(True)
    test_random_sampler_multi_iter(True)
    test_sampler_py_api()
    test_python_sampler()
