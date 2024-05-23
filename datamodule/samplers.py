from operator import itemgetter
from typing import Iterator, Optional

import numpy as np
import torch

from fairseq.data import data_utils
from torch.utils.data import Dataset, DistributedSampler, RandomSampler
from torch.utils.data.sampler import Sampler


class ByFrameCountSampler(Sampler):
    def __init__(self, dataset, max_frames_per_gpu, shuffle=True, seed=0):
        self.dataset = dataset
        self.max_frames_per_gpu = max_frames_per_gpu
        self.sizes = [item[2] for item in self.dataset.list]

        self.shuffle = shuffle
        self.seed = seed
        self.epoch = 0
        
        batch_indices = data_utils.batch_by_size(
            self._get_indices(), lambda i: self.sizes[i], max_tokens=max_frames_per_gpu
        )
        self.num_batches = len(batch_indices)

    def _get_indices(self):
        if self.shuffle:  # shuffles indices corresponding to equal lengths
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch)
            order = [torch.randperm(len(self.dataset), generator=g).tolist()]
        else:
            order = [list(range(len(self.dataset)))]
        order.append(self.sizes)
        return np.lexsort(order)[::-1]

    def __len__(self):
        return self.num_batches

    def __iter__(self):
        batch_indices = data_utils.batch_by_size(
            self._get_indices(),
            lambda i: self.sizes[i],
            max_tokens=self.max_frames_per_gpu,
        )
        return iter(batch_indices)

    def set_epoch(self, epoch):
        self.epoch = epoch


class ByFrameCountSamplerMultilang(Sampler):
    def __init__(self, dataset, max_frames_per_gpu, shuffle=True, seed=0, max_language_token=6):
        self.dataset = dataset
        self.max_frames_per_gpu = max_frames_per_gpu
        
        total_size = 0
        sizes = []
        dataset_new = []
        ### All language tokens assumed to be in the beginning. Starting from 2. 
        for j in range(2, max_language_token + 1):
            size_j = [item[2] for item in self.dataset.list if item[3][0].item()==j]
            sizes.append(size_j)
            total_size += sum(size_j)
            data_j = [k for k,item in enumerate(self.dataset.list) if item[3][0].item()==j]
            dataset_new.append(data_j)
        self.dataset_idx = dataset_new
        self.sizes = sizes
        self.shuffle = shuffle
        self.seed = seed
        self.epoch = 0
        
        batch_indices = []
        for j in range(len(self.sizes)):
            if len(self.sizes[j]) > 0:
                batch_ind_j = data_utils.batch_by_size(self._get_indices(j), lambda i: self.sizes[j][i], max_tokens=max_frames_per_gpu)
                batch_ind_new = [0]*len(batch_ind_j)
                for bk, bval in enumerate(batch_ind_j):
                    batch_ind_new[bk] = np.array([self.dataset_idx[j][bvali] for bvali in bval], dtype=np.int64)
                batch_indices += batch_ind_new
        
        batch_indices = batch_indices
        self.num_batches = len(batch_indices)
        

    def _get_indices(self, j):
        if self.shuffle:  # shuffles indices corresponding to equal lengths
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch)
            order = [torch.randperm(len(self.dataset_idx[j]), generator=g).tolist()]
        else:
            order = [self.dataset_idx[j]]
        order.append(self.sizes[j])
        return np.lexsort(order)[::-1]

    def __len__(self):
        return self.num_batches

    def __iter__(self):
        batch_indices = []
        for j in range(len(self.sizes)):
            batch_ind_j = data_utils.batch_by_size(self._get_indices(j), lambda i: self.sizes[j][i], max_tokens=self.max_frames_per_gpu)
            batch_ind_new = [0]*len(batch_ind_j)
            for bk, bval in enumerate(batch_ind_j):
                batch_ind_new[bk] = np.array([self.dataset_idx[j][bvali] for bvali in bval], dtype=np.int64)
            batch_indices += batch_ind_new
        
        return iter(batch_indices)

    def set_epoch(self, epoch):
        self.epoch = epoch


class DatasetFromSampler(Dataset):
    """Dataset to create indexes from `Sampler`.
    Args:
        sampler: PyTorch sampler
    """

    def __init__(self, sampler: Sampler):
        """Initialisation for DatasetFromSampler."""
        self.sampler = sampler
        self.sampler_list = None

    def __getitem__(self, index: int):
        """Gets element of the dataset.
        Args:
            index: index of the element in the dataset
        Returns:
            Single element by index
        """
        if self.sampler_list is None:
            self.sampler_list = list(self.sampler)
        return self.sampler_list[index]

    def __len__(self) -> int:
        """
        Returns:
            int: length of the dataset
        """
        return len(self.sampler)


class DistributedSamplerWrapper(DistributedSampler):
    """
    Wrapper over `Sampler` for distributed training.
    Allows you to use any sampler in distributed mode.
    It is especially useful in conjunction with
    `torch.nn.parallel.DistributedDataParallel`. In such case, each
    process can pass a DistributedSamplerWrapper instance as a DataLoader
    sampler, and load a subset of subsampled data of the original dataset
    that is exclusive to it.
    .. note::
        Sampler is assumed to be of constant size.
    """

    def __init__(
        self,
        sampler,
        num_replicas: Optional[int] = None,
        rank: Optional[int] = None,
        shuffle: bool = True,
        drop_last: bool = False,
    ):
        """
        Args:
            sampler: Sampler used for subsampling
            num_replicas (int, optional): Number of processes participating in
                distributed training
            rank (int, optional): Rank of the current process
                within ``num_replicas``
            shuffle (bool, optional): If true (default),
                sampler will shuffle the indices
        """
        super(DistributedSamplerWrapper, self).__init__(
            DatasetFromSampler(sampler),
            num_replicas=num_replicas,
            rank=rank,
            shuffle=shuffle,
            drop_last=drop_last,
        )
        self.sampler = sampler

    def __iter__(self) -> Iterator[int]:
        """Iterate over sampler.
        Returns:
            python iterator
        """
        self.dataset = DatasetFromSampler(self.sampler)
        indexes_of_indexes = super().__iter__()

        subsampler_indexes = self.dataset
        return iter(itemgetter(*indexes_of_indexes)(subsampler_indexes))

    def set_epoch(self, epoch):
        super().set_epoch(epoch)
        self.sampler.set_epoch(epoch)


class RandomSamplerWrapper(RandomSampler):
    def __init__(self, sampler):
        super(RandomSamplerWrapper, self).__init__(DatasetFromSampler(sampler))
        self.sampler = sampler

    def __iter__(self) -> Iterator[int]:
        """Iterate over sampler.
        Returns:
            python iterator
        """
        self.dataset = DatasetFromSampler(self.sampler)
        indexes_of_indexes = super().__iter__()
        subsampler_indexes = self.dataset
        return iter(itemgetter(*indexes_of_indexes)(subsampler_indexes))
