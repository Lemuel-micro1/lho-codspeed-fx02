import math

from voyagekit import core


def test_parse_line():
    assert core.parse_line("211000001,60,40.5,13.2,12.5") == (211000001, 60, 40.5, 13.2, 12.5)


def test_parse_log_skips_comments_and_blank_lines():
    text = "# header\n211000001,0,40.0,13.0,10.0\n\n211000001,300,40.1,13.0,10.0"
    assert len(core.parse_log(text)) == 2


def test_one_degree_of_latitude_is_about_60_nm():
    assert math.isclose(core.haversine_nm(0, 0, 1, 0), 60.04, rel_tol=1e-3)


def test_synthetic_log_is_deterministic():
    assert core.synthetic_log(500) == core.synthetic_log(500)


def test_track_distance_and_speed_alerts():
    records = core.parse_log(core.synthetic_log(2000))
    assert len(core.track_distance(records)) == 50
    assert len(core.speed_alerts(records)) > 0