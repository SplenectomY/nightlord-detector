from nightlord_detector.match import match_boss


def test_matches_bell_bearing_hunter():
    hit = match_boss("Bell Bearing Hunter")
    assert hit is not None
    assert hit.key == "bbh"
    assert hit.night == 1


def test_matches_japanese_bell_bearing_hunter():
    hit = match_boss("鈴玉狩り")
    assert hit is not None
    assert hit.key == "bbh"


def test_matches_korean_battlefield_commander():
    hit = match_boss("전장의 노장")
    assert hit is not None
    assert hit.key == "battlefield"


def test_matches_simplified_chinese_grafted_monarch():
    hit = match_boss("接肢君王")
    assert hit is not None
    assert hit.key == "grafted"


def test_draconic_not_regular_tree_sentinel():
    hit = match_boss("Draconic Tree Sentinel")
    assert hit is not None
    assert hit.key == "draconic"
    assert hit.night == 2


def test_japanese_draconic_not_plain_tree_sentinel():
    hit = match_boss("竜のツリーガード")
    assert hit is not None
    assert hit.key == "draconic"


def test_mohg_alias():
    hit = match_boss("Mohg, Lord of Blood")
    assert hit is not None
    assert hit.key == "mohg"


def test_chinese_mohg():
    hit = match_boss("鲜血君王")
    assert hit is not None
    assert hit.key == "mohg"
