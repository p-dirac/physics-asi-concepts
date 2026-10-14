"""
Fits a given ModelFamily to training data via nonlinear least squares and
scores it on held-out data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from data.generator import Dataset
from models.families import ModelFamily


@dataclass
class FitResult:
    family_name: str
    params: list[float]
    train_rmse: float
    test_rmse: float
    fit_succeeded: bool


class ModelFitter:
    def __init__(self, dataset: Dataset, max_fit_evaluations: int = 10000):
        self.dataset = dataset
        self.max_fit_evaluations = max_fit_evaluations

    def fit(self, family: ModelFamily) -> FitResult:
        try:
            params, _ = curve_fit(
                family.fn, self.dataset.x_train, self.dataset.y_train,
                p0=family.initial_guess, maxfev=self.max_fit_evaluations,
            )
            train_pred = family.fn(self.dataset.x_train, *params)
            test_pred = family.fn(self.dataset.x_test, *params)
            train_rmse = float(np.sqrt(np.mean((train_pred - self.dataset.y_train) ** 2)))
            test_rmse = float(np.sqrt(np.mean((test_pred - self.dataset.y_test) ** 2)))
            return FitResult(family.name, list(params), train_rmse, test_rmse, True)
        except RuntimeError:
            # curve_fit failed to converge -- a legitimate outcome for a
            # badly-mismatched family (e.g. fitting a bounded sinusoid's
            # amplitude/frequency to monotonically decaying data can fail
            # to converge at all), scored as maximally bad rather than
            # crashing the loop.
            return FitResult(family.name, [], float("inf"), float("inf"), False)
