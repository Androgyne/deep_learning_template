import torch.utils.data
from torch.utils.data.dataset import ConcatDataset

from deep_learning_template.utils.imports import import_file
from . import datasets as D
from .collators.build import make_batch_collator
from .transforms import build_transforms


def build_dataset(dataset_list, transforms, dataset_catalog, is_train=True, ds_len=-1):
    if not isinstance(dataset_list, (list, tuple)):
        raise RuntimeError(
            "dataset_list should be a list of strings, got {}".format(dataset_list)
        )
    datasets = []
    for dataset_name in dataset_list:
        data = dataset_catalog.get(dataset_name)
        factory = getattr(D, data["factory"])
        args = data["args"]
        args['ds_len'] = ds_len
        args["transforms"] = transforms
        dataset = factory(**args)
        datasets.append(dataset)

    dataset = datasets[0]
    if len(datasets) > 1:
        dataset = ConcatDataset(datasets)

    return [dataset]


def make_data_loader(cfg, is_train=True):
    if is_train:
        batch_size = cfg.solver.batch_size
        shuffle = cfg.input.shuffle
    else:
        batch_size = cfg.test.batch_size
        shuffle = False

    paths_catalog = import_file(
        "deep_learning_template.config.paths_catalog", cfg.paths_catalog, True
    )
    DatasetCatalog = paths_catalog.DatasetCatalog
    dataset_list = cfg.datasets.train if is_train else cfg.datasets.test

    transforms = build_transforms(cfg, is_train)
    datasets = build_dataset(dataset_list, transforms, DatasetCatalog, is_train)

    data_loaders = []
    for dataset in datasets:
        collator = make_batch_collator(cfg)
        num_workers = cfg.dataloader.num_workers
        data_loader = torch.utils.data.DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=collator,
        )
        data_loaders.append(data_loader)
    assert len(data_loaders) == 1
    return data_loaders[0]