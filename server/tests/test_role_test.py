import pytest

from app.role_test import questions, score


def test_questions_shape():
    qs = questions()
    assert len(qs) == 10 and all(len(q["options"]) == 4 for q in qs)
    assert "correct" not in str(qs)  # верные ответы мини-задач не уходят на клиент


def test_score_picks_top_and_smart():
    r = score([1, 1, 0, 1, 1, 1, 2, 1, 2, 2])
    assert r["top"] == "msg" and r["scores"]["msg"] == 6 and r["smart"] == 2


def test_score_validates():
    with pytest.raises(ValueError):
        score([0] * 9)
    with pytest.raises(ValueError):
        score([0] * 9 + [4])
