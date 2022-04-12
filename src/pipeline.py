from typing import Iterable

from more_itertools import last

from src.stages.stage import Stage
from src.utils import tqdm, tupled


class Pipeline:
    def __init__(self, stages: Iterable[Stage], generator=False, verbose=None):
        self.stages = list(stages)
        self.verbose = verbose
        self.generator = generator

    def apply(self, *args, orient='rows'):
        if orient == 'cols':
            args = zip(*args)

        for stage in self.stages:
            try:
                verbose = self.verbose or stage.verbose
                args = tqdm(args, desc=stage.__class__.__name__) if verbose else args

                apply = tupled(stage.apply, input=True, output=stage != last(self.stages))

                if stage.collect_inputs:
                    args = apply(list(zip(*args)))
                else:
                    args = map(apply, args)

                if not self.generator:
                    args = list(args)

            except Exception as e:
                print(f'Error in {stage.__class__.__name__}: {e}')
                print(f'Args: {args}')
                raise e

        return args
