from app.ml.labeling import soh_to_class


def test_good_boundary_above():
    assert soh_to_class(85.0) == "GOOD"


def test_good_boundary_just_below():
    assert soh_to_class(84.9) == "MONITOR"


def test_monitor_boundary_above():
    assert soh_to_class(70.0) == "MONITOR"


def test_monitor_boundary_just_below():
    assert soh_to_class(69.9) == "CRITICAL"


def test_good_high_value():
    assert soh_to_class(100.0) == "GOOD"


def test_critical_low_value():
    assert soh_to_class(47.77) == "CRITICAL"
