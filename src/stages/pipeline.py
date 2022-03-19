from typing import Iterable

from src.stages.stage import Stage
from src.utils.utils import progressbar, tupled


class Pipeline:
    def __init__(self, stages: Iterable[Stage], generator=False, verbose=None):
        self.stages = list(stages)
        self.verbose = verbose
        self.generator = generator

    def apply(self, *args):
        args = args if self.stages[0].collect_inputs else zip(*args)
        unpack = True
        for stage in self.stages:
            try:
                verbose = stage.verbose if self.verbose is None else self.verbose
                args = progressbar(args) if verbose else args

                apply = tupled(stage.apply) if unpack else stage.apply

                if stage.collect_inputs:
                    args = apply(list(args))
                else:
                    args = map(apply, args)

                if not self.generator:
                    args = list(args)

            except Exception as e:
                print(f'Error: call {stage} {args}')
                raise e

            unpack = stage.unpack_result

        return args
