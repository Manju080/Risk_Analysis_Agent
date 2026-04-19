"""
Unit tests for isk_agent.py — pure math, no network calls mocked.
Run: pytest tests/test_risk_agent.py -v
"""

import pytest
import pandas as pd
import numpy as np
from agents.risk_agent import calculate_var, calculate_sharpe, calculate_beta
from core.settings import Settings


@pytest.fixture
def flat_returns():
    """Zero-variance series — Sharpe should be 0."""
    return pd.Series([0.001] * 252)


@pytest.fixture
def known_returns():
    """Controlled series with known statistical properties."""
    np.random.seed(42)
    return pd.Series(np.random.normal(0.001, 0.02, 252))


@pytest.fixture
def market_returns():
    np.random.seed(99)
    return pd.Series(np.random.normal(0.0008, 0.015, 252))


def test_var_is_positive(known_returns):
    var = calculate_var(known_returns)
    assert var > 0, "VaR should be a positive percentage"


def test_var_between_0_and_20(known_returns):
    var = calculate_var(known_returns)
    assert 0 < var < 20, f"VaR={var} looks unrealistic"


def test_var_higher_confidence_is_larger(known_returns):
    var_95 = calculate_var(known_returns, confidence=0.95)
    var_99 = calculate_var(known_returns, confidence=0.99)
    assert var_99 >= var_95, "99% VaR must be >= 95% VaR"


def test_var_requires_min_30_points():
    with pytest.raises(ValueError):
        calculate_var(pd.Series([0.01]*10))


def test_sharpe_flat_returns_is_zero(flat_returns):
    sharpe = calculate_sharpe(flat_returns, risk_free_rate=0.065)
    assert abs(sharpe) < 0.1, f"Flat returns should give ~0 Sharpe, got {
        sharpe}"


def test_sharpe_positive_for_good_returns():
    # Needs variation — flat series has undefined Sharpe (std ≈ 0)
    # Simulate strong positive returns with realistic noise
    np.random.seed(7)
    good = pd.Series(np.random.normal(loc=0.005, scale=0.01, size=252))
    assert calculate_sharpe(good) > 1.0


def test_beta_perfectly_correlated():
    returns = pd.Series(np.random.normal(0, 0.01, 252))
    beta = calculate_beta(returns, returns)   # beta with itself = 1.0
    assert abs(beta - 1.0) < 0.01


def test_beta_requires_min_30_points():
    short = pd.Series([0.01] * 20)
    with pytest.raises(ValueError):
        calculate_beta(short, short)


def test_beta_uncorrelated_near_zero(known_returns, market_returns):
    # Independent series — beta should be small (not guaranteed 0, but small)
    beta = calculate_beta(known_returns, market_returns)
    assert -2 < beta < 2, f"Beta={beta} seems extreme for uncorrelated series"
