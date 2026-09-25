from nightlord_detector.match import match_boss


def test_matches_bell_bearing_hunter():
    hit = match_boss("Bell Bearing Hunter")
    assert hit is not None
    assert hit.key == "bbh"
    assert hit.night == 1


def test_draconic_not_regular_tree_sentinel():
    hit = match_boss("Draconic Tree Sentinel")
    assert hit is not None
    assert hit.key == "draconic"
    assert hit.night == 2


def test_mohg_alias():
    hit = match_boss("Mohg, Lord of Blood")
    assert hit is not None
    assert hit.key == "mohg"
