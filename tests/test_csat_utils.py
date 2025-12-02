import os
import sys
import math
import pytest

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from csat_utils import (
    SENTIMENT_PRESETS,
    apply_distribution,
    responses_per_year,
    ces,
    total_cost,
    avg_cost_per_response,
    annual_csat_cost,
    minutes_to_cost,
)


def test_sentiment_presets_exist_and_sum_to_1():
    assert "Customers mostly happy" in SENTIMENT_PRESETS
    assert "Customer ambivalent" in SENTIMENT_PRESETS
    assert "Customers mostly unhappy" in SENTIMENT_PRESETS
    for label, dist in SENTIMENT_PRESETS.items():
        h, n, s = dist.as_tuple()
        assert all(0.0 <= x <= 1.0 for x in (h, n, s))
        assert math.isclose(h + n + s, 1.0, rel_tol=1e-9)


def test_apply_distribution_happy_case_keeps_total():
    total = 1000
    h, n, s = apply_distribution(total, "Customers mostly happy")
    assert h + n + s == total
    # ~60/30/10 split
    assert abs(h - 600) <= 1
    assert abs(n - 300) <= 1
    assert s >= 0


def test_apply_distribution_ambivalent_case_keeps_total():
    total = 123
    h, n, s = apply_distribution(total, "Customer ambivalent")
    assert h + n + s == total
    # Roughly thirds
    assert abs(h - total/3) <= 1
    assert abs(n - total/3) <= 1
    assert s >= 0


def test_apply_distribution_unhappy_case_keeps_total():
    total = 789
    h, n, s = apply_distribution(total, "Customers mostly unhappy")
    assert h + n + s == total
    assert s >= n >= h  # monotonic in this preset


def test_responses_per_year_basic_and_bounds():
    r = responses_per_year(10.0, 1.5, 100.0)
    assert r == 10.0 * 12.0 * 1.5 * 1.0
    r2 = responses_per_year(10.0, 1.0, 0.0)
    assert r2 == 0.0
    r3 = responses_per_year(10.0, 1.0, 200.0)  # clip to 100%
    assert r3 == 10.0 * 12.0 * 1.0 * 1.0


def test_ces_computation_and_none_on_zero_total():
    assert ces(60, 10, 100) == pytest.approx((60 - 10) / 100)
    assert ces(0, 0, 0) is None


def test_costs_and_annualization():
    h, n, s = 60, 30, 10
    w_h, w_n, w_s = 0.0, 15.0, 25.0
    tcost = total_cost(h, n, s, w_h, w_n, w_s)
    assert tcost == (60*0.0) + (30*15.0) + (10*25.0)

    avg = avg_cost_per_response(tcost, h + n + s)
    assert avg == pytest.approx(tcost / (h + n + s))

    ann = annual_csat_cost(avg, 1200.0)
    assert ann == pytest.approx(avg * 1200.0)

    assert avg_cost_per_response(100.0, 0) is None


def test_minutes_to_cost():
    assert minutes_to_cost(30, 100.0) == pytest.approx(50.0)
    assert minutes_to_cost(0, 100.0) == 0.0
    assert minutes_to_cost(15, 80.0) == pytest.approx(20.0)
