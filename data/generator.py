"""
Synthetic 'physical law' data: a true generating function plus Gaussian
noise, split into train/test. The split is not optional -- in-sample error
is monotonically non-increasing in model flexibility by construction, so it
can never reveal that a family is wrong or overfit. Only held-out error can.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class Dataset:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    x_all: np.ndarray
    y_all: np.ndarray


class DataGenerator:
    """Draws one dataset from a true function plus noise. `true_function`
    is meant to mimic a physical law with a dominant leading-order term and
    a smaller correction -- e.g. `2/x**2 + correction/x**3`. For two decaying
    power laws like this, the correction is proportionally LARGEST at small
    x and smallest at large x (correction/leading = correction_coeff/(2x),
    which shrinks as x grows) -- not "negligible near the origin," which
    would only be true for a correction that *grows* with x (like a
    polynomial term such as x**5), not one that decays. This actually still
    mirrors general relativity reasonably well: post-Newtonian corrections
    to gravity are largest in the strong-field regime close to the source
    (small r -- Mercury has the largest perihelion precession because it's
    the innermost planet, not the outermost) and negligible far away (large
    r). The model families that later try to fit this data never see this
    function -- they only see the noisy (x, y) points."""

    def __init__(
        self,
        true_function: Callable[[np.ndarray], np.ndarray],
        noise_sigma: float = 0.03,
        x_min: float = 1.0,
        x_max: float = 6.0,
        n_points: int = 60,
        train_fraction: float = 0.667,
        seed: int = 1,
    ):
        self.true_function = true_function
        self.noise_sigma = noise_sigma
        self.x_min = x_min
        self.x_max = x_max
        self.n_points = n_points
        self.train_fraction = train_fraction
        self.seed = seed

    def generate(self) -> Dataset:
        rng = np.random.default_rng(self.seed)
        x = np.linspace(self.x_min, self.x_max, self.n_points)
        y = self.true_function(x) + rng.normal(0, self.noise_sigma, size=x.shape)

        idx = rng.permutation(len(x))
        split = int(len(x) * self.train_fraction)
        train_idx, test_idx = idx[:split], idx[split:]

        return Dataset(
            x_train=x[train_idx], y_train=y[train_idx],
            x_test=x[test_idx], y_test=y[test_idx],
            x_all=x, y_all=y,
        )
