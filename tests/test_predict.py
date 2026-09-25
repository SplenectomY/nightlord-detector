from nightlord_detector.predict import predict


def test_warrior_mohg_locks_balancers():
    result = predict("warrior", "mohg", "d5")
    assert result.locked
    assert result.guesses[0].key == "balancers"
    assert result.guesses[0].pct > 99


def test_demi_alone_is_gladius_or_heolstor():
    result = predict("demi", None, "any")
    keys = {g.key for g in result.guesses}
    assert keys == {"gladius", "heolstor"}


def test_demi_fell_stays_gladius_or_heolstor():
    result = predict("demi", "fell", "d4")
    keys = {g.key for g in result.guesses}
    assert keys == {"gladius", "heolstor"}
    assert not result.locked


def test_deathknight_locks_dreglord():
    result = predict("deathknight", None, "any")
    assert result.locked
    assert result.guesses[0].key == "dreglord"


def test_impossible_pair_is_empty():
    result = predict("warrior", "artorias", "any")
    assert result.guesses == ()
