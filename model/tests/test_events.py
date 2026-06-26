"""TDD: event-year resolution and year->phase mapping."""
import pytest
from finmodel import schema, events


@pytest.fixture
def cfg():
    return schema.load_config()


def test_resolve_events_to_years(cfg):
    ev = events.resolve_events(cfg)
    assert ev["person2_retires"] == 2031
    assert ev["person1_retires"] == 2040
    assert ev["inheritance"] == 2036
    assert ev["horizon"] == 2072


def test_phase_for_year_boundaries(cfg):
    assert events.phase_for_year(cfg, 2026)["name"] == "working"
    assert events.phase_for_year(cfg, 2030)["name"] == "working"
    assert events.phase_for_year(cfg, 2031)["name"] == "person1_only"
    assert events.phase_for_year(cfg, 2036)["name"] == "person1_only"
    assert events.phase_for_year(cfg, 2040)["name"] == "retired"
    assert events.phase_for_year(cfg, 2072)["name"] == "retired"


def test_retirement_year_helper(cfg):
    assert events.retirement_year(cfg) == 2040


def test_changing_person1_retires_cascades_phase(cfg):
    # Retire earlier: move Person 1's retirement to 2038; the retired phase should follow.
    cfg2 = schema.load_config(scenario=None)
    cfg2.events["person1_retires"]["year"] = 2038
    assert events.retirement_year(cfg2) == 2038
    assert events.phase_for_year(cfg2, 2037)["name"] == "person1_only"
    assert events.phase_for_year(cfg2, 2038)["name"] == "retired"


def test_events_of_type(cfg):
    accesses = events.events_of_type(cfg, "super_access")
    assert {e["person"] for e in accesses} == {"person2", "person1"}
