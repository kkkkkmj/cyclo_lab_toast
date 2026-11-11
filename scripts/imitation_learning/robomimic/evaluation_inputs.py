"""Single-environment evaluation input contract; no simulator imports."""
import functools
import json
from pathlib import Path

import numpy as np
import torch


def trace(path, stage, **values):
    if path is not None:
        with Path(path).open('a') as stream:
            stream.write(json.dumps(dict(stage=stage, **values)) + '\n')


def prepare_observations(raw, image_keys, expected_shapes, trace_path=None):
    """Remove exactly the one environment axis; preserve all feature axes."""
    obs = {}
    details = {}
    for key, expected in expected_shapes.items():
        if key not in raw:
            raise KeyError(f'Missing required observation: {key}')
        value = raw[key]
        if not isinstance(value, torch.Tensor) or value.ndim < 2 or value.shape[0] != 1:
            raise ValueError(f'{key}: expected a tensor with one environment, got {getattr(value, "shape", None)}')
        single = value[0]
        if key in image_keys:
            if single.ndim != 3 or single.shape[-1] != 3 or single.dtype != torch.uint8:
                raise ValueError(f'{key}: expected raw uint8 HWC RGB, got {single.shape}, {single.dtype}')
            single = single.permute(2, 0, 1).to(dtype=torch.float32) / 255.0
        if tuple(single.shape) != tuple(expected):
            raise ValueError(f'{key}: processed shape {tuple(single.shape)} != checkpoint {tuple(expected)}')
        if not torch.isfinite(single).all():
            raise ValueError(f'{key}: non-finite observation')
        obs[key] = single
        details[key] = dict(raw_shape=list(value.shape), raw_dtype=str(value.dtype),
                            processed_shape=list(single.shape), expected_shape=list(expected),
                            processed_min=float(single.min()), processed_max=float(single.max()))
    trace(trace_path, 'observations', keys=details)
    return obs


def restore_actions(actions, minimum, maximum):
    """Apply the project's scalar global min/max inverse exactly once."""
    if (minimum is None) != (maximum is None):
        raise ValueError('Both action normalization limits must be supplied together')
    if actions.ndim != 1 or not np.isfinite(actions).all():
        raise ValueError(f'Expected finite unbatched action vector, got {actions.shape}')
    if minimum is None:
        return actions
    if not np.isfinite([minimum, maximum]).all() or maximum <= minimum:
        raise ValueError('Invalid global action normalization range')
    return (actions + 1) * (maximum - minimum) / 2 + minimum


def install_policy_shape_trace(policy, path):
    """Observe the real batch/time axes entering the RNN, without transforming them."""
    if path is None:
        return
    actor = policy.policy.nets['policy']
    original = actor.forward_train

    @functools.wraps(original)
    def traced(*args, **kwargs):
        observations = kwargs.get('obs_dict', args[0] if args else None)
        trace(path, 'policy_sequence', shapes={k: list(v.shape) for k, v in observations.items()})
        return original(*args, **kwargs)

    actor.forward_train = traced
