# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""er_skill_draft.py 규칙 검사 (지어낸 설명으로): python3 -I -B -m unittest discover -s scripts/er-sheet -p "test_*.py" """
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_effect
from er_skill_draft import draft, read_tags

CAT = {"물리": "PHYSICAL", "스증": "SPECIAL", "변화": "STATUS"}


class DraftRules(unittest.TestCase):
    def check(self, d):
        skill_effect.parse(d["effect"], CAT[d["cat"]], d["prio"])  # 못 읽으면 여기서 에러

    def test_attack_category_by_coef(self):
        d = draft("BRUISER", "Q", "적에게 N의 스킬 피해를 입힙니다.", "N(+스킬 증폭의 N)의 스킬 피해")
        self.assertEqual((d["cat"], d["effect"], d["power"]), ("스증", "피해", 60))
        d = draft("MAGE", "Q", "적에게 N의 스킬 피해를 입힙니다.", "N(+공격력의 N)의 스킬 피해")
        self.assertEqual(d["cat"], "물리")
        self.check(d)

    def test_stun_slow_and_dash(self):
        d = draft("ASSASSIN", "E", "지정한 방향으로 돌진하며 N의 스킬 피해를 입히고 N초 동안 기절시키며 이동 속도를 N 감소시킵니다.", "(+공격력의 N)")
        self.assertEqual(d["effect"], "선공(+1) 피해 + 30% 스턴 + 상대 속도 1단계 ↓")
        self.assertEqual(d["prio"], 1)
        self.assertLessEqual(d["power"], 50)
        self.check(d)

    def test_slow_only_on_w_is_paralysis(self):
        d = draft("MAGE", "W", "N의 스킬 피해를 입히고 이동 속도를 N 감소시킵니다.", "(+스킬 증폭의 N)")
        self.assertEqual(d["effect"], "피해 + 30% 둔화")
        self.check(d)

    def test_status_skills(self):
        d = draft("TANK", "W", "N초 동안 N의 피해를 막아주는 보호막을 얻습니다.", "")
        self.assertEqual((d["cat"], d["effect"]), ("변화", "방어 · 스킬 저항 1단계 ↑"))
        self.check(d)
        d = draft("SUPPORT", "W", "아군의 체력을 N 회복시킵니다.", "")
        self.assertEqual(d["effect"], "체력 50% 회복")
        self.check(d)
        d = draft("MAGE", "Q", "덫을 설치합니다. 밟은 적은 N초 동안 속박됩니다.", "")
        self.assertEqual((d["effect"], d["acc"]), ("둔화", 90))
        self.check(d)
        d = draft("ASSASSIN", "E", "아무 일도 없는 설명.", "")
        self.assertEqual(d["effect"], "속도 2단계 ↑")
        self.check(d)

    def test_drain_not_double_counted(self):
        self.assertEqual(read_tags("N의 스킬 피해를 입히고 입힌 피해량의 N만큼 체력을 회복합니다."), ["피해", "흡수"])
        d = draft("BRUISER", "R", "N의 스킬 피해를 입히고 입힌 피해량의 N만큼 체력을 회복합니다.", "(+공격력의 N)")
        self.assertEqual(d["effect"], "피해 + 피해의 50% 회복")
        self.assertGreaterEqual(d["power"], 90)
        self.check(d)

    def test_forced_attack(self):
        d = draft("SUPPORT", "R", "N초 동안 무적 상태가 됩니다.", "", force_attack=True)
        self.assertNotEqual(d["cat"], "변화")
        self.check(d)


if __name__ == "__main__":
    unittest.main()
