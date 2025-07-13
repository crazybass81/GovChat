import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lib.matching.extract_policy_conditions import extract_policy_conditions


def test_age_extract():
    txt = "지원대상: 만 39세 이하 서울 거주 청년"
    cond = extract_policy_conditions(txt)
    assert cond["age"]["max"] == 39
    assert cond["region"] == "서울"
