"""CPU workloads; data preparation and validation are outside measurement."""

from dataclasses import dataclass
import math
import random

import pytest

from voyagekit import core


@dataclass(frozen=True)
class Scenario:
    size: int
    vessels: int
    shuffled: bool
    distance_nm: float
    alert_count: int


# Baselines from seed=7, max_knots=30.0. Named IDs stay stable across runs.
SCENARIOS = [
    pytest.param(Scenario(1_000, 50, False, 414.2262190353, 16), id="1k-50-vessels"),
    pytest.param(Scenario(20_000, 50, False, 5801.5530873452, 207), id="20k-50-vessels"),
    pytest.param(Scenario(20_000, 50, True, 5801.5530873452, 207), id="20k-shuffled"),
    pytest.param(Scenario(20_000, 1, False, 6208.7957435127, 16426), id="20k-single-vessel"),
]


@pytest.fixture(scope="module", params=SCENARIOS)
def workload(request):
    scenario = request.param
    lines = core.synthetic_log(scenario.size, scenario.vessels, seed=7).splitlines()
    if scenario.shuffled:
        random.Random(11).shuffle(lines)
    # Include skipped lines without measuring their construction.
    text = "# AIS position fixes\n\n" + "\n".join(lines) + "\n\n"
    records = core.parse_log(text)
    return scenario, text, records


def assert_distances(totals, scenario):
    assert set(totals) == set(range(200000000, 200000000 + scenario.vessels))
    assert all(math.isfinite(value) and value > 0 for value in totals.values())
    assert math.fsum(totals.values()) == pytest.approx(scenario.distance_nm, rel=1e-9)


def assert_alerts(alerts, scenario):
    assert len(alerts) == scenario.alert_count
    assert len(set(alerts)) == len(alerts)
    assert all(
        200000000 <= mmsi < 200000000 + scenario.vessels
        and 0 < timestamp < scenario.size * 6
        and timestamp % 6 == 0
        for mmsi, timestamp in alerts
    )


def test_parse_log(benchmark, workload):
    scenario, text, records = workload
    result = benchmark(core.parse_log, text)
    assert len(result) == scenario.size
    assert result == records


def test_group_by_vessel(benchmark, workload):
    scenario, _, records = workload
    tracks = benchmark(core.group_by_vessel, records)
    assert len(tracks) == scenario.vessels
    for mmsi, fixes in tracks.items():
        vessel_index = mmsi - 200000000
        assert 0 <= vessel_index < scenario.vessels
        assert all(fix[0] == mmsi for fix in fixes)
        assert [fix[1] for fix in fixes] == list(
            range(vessel_index * 6, scenario.size * 6, scenario.vessels * 6)
        )


def test_track_distance(benchmark, workload):
    scenario, _, records = workload
    totals = benchmark(core.track_distance, records)
    assert_distances(totals, scenario)


def test_speed_alerts(benchmark, workload):
    scenario, _, records = workload
    alerts = benchmark(core.speed_alerts, records, max_knots=30.0)
    assert_alerts(alerts, scenario)


@pytest.fixture(scope="module")
def pipeline_workload():
    scenario = Scenario(20_000, 50, False, 5801.5530873452, 207)
    return scenario, core.synthetic_log(scenario.size, scenario.vessels, seed=7)


def summary_pipeline(text):
    return core.track_distance(core.parse_log(text))


def alerts_pipeline(text):
    return core.speed_alerts(core.parse_log(text), max_knots=30.0)


def test_summary_pipeline(benchmark, pipeline_workload):
    scenario, text = pipeline_workload
    assert_distances(benchmark(summary_pipeline, text), scenario)


def test_alerts_pipeline(benchmark, pipeline_workload):
    scenario, text = pipeline_workload
    assert_alerts(benchmark(alerts_pipeline, text), scenario)
