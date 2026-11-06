# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""팬키트 음성 파일 이름 → 스킬 키 규칙 검사

python3 -m unittest discover -s scripts/fankit -p "test_*.py"
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_voice import pick, voice_key, zip_lang  # noqa: E402


class VoiceKeyTest(unittest.TestCase):
    def test_skill_letters(self) -> None:
        # 실험체마다 다른 이름 모양 (팬키트에서 실제로 본 것들)
        cases = {
            "Alex_skillQ1.wav": "q",
            "isol_skillQ_1_en.wav": "q",
            "silvia_skillE1_01.wav": "e",
            "Estelle_skillE1-solo-1_01.wav": "e",
            "Piolo_skillW1-1_01.wav": "w",
            "Lenox _skillR1.wav": "r",
            "charlotte_skillW0_1_01.wav": "w",
            "magnus_skillPassive1.wav": "passive",
        }
        for name, key in cases.items():
            self.assertEqual(voice_key(name), key, name)

    def test_skill_codes(self) -> None:
        # 10XX200 = Q · 300 = W · 400 = E · 500 = R (XX = ER 번호)
        self.assertEqual(voice_key("Emma_PlaySkill1019200seq0_1_en.wav"), "q")
        self.assertEqual(voice_key("Bernice_PlaySkill1025300seq0_2_ko.wav"), "w")
        self.assertEqual(voice_key("Bihyung_PlaySkill1088400seq0_1_ja.wav"), "e")
        self.assertEqual(voice_key("Bihyung_PlaySkill1088500seq0_3_ja.wav"), "r")
        self.assertEqual(voice_key("Bihyung_PlaySkill1088210seq0_1_ja.wav"), "q")

    def test_other_lines(self) -> None:
        self.assertEqual(voice_key("jackie_selected_ko_01.wav"), "select")
        self.assertEqual(voice_key("fiora_selected .wav"), "select")
        self.assertEqual(voice_key("036. magnus_firstMove_1_en.wav"), "firstmove")
        # 무기 스킬 · 다른 대사는 안 써요
        self.assertIsNone(voice_key("jackie_learnweaponskill_Axe_1_ko.wav"))
        self.assertIsNone(voice_key("fiora_weaponskill1_1.wav"))
        self.assertIsNone(voice_key("fiora_killPlayer1-1.wav"))
        self.assertIsNone(voice_key("Lenox _taunt_Yuki.wav"))

    def test_pick_up_to_three(self) -> None:
        got = pick(
            [
                "Aiden_skillE1-2_01.wav",
                "Aiden_skillE1_01.wav",
                "Bihyung_PlaySkill1088210seq0_1_ja.wav",
                "Bihyung_PlaySkill1088200seq0_2_ja.wav",
                "Bihyung_PlaySkill1088200seq0_1_ja.wav",
                "magnus_selected_animation2.wav",
                "magnus_selected_animation.wav",
                "magnus_selected_en.wav",
                "jackie_skillR_3_ko.wav",
                "jackie_skillR_1_ko.wav",
                "jackie_skillR_2_ko.wav",
                "jackie_skillR_4_ko.wav",
                "desktop.ini",
            ]
        )
        # 숫자가 작은 것부터 최대 3개
        self.assertEqual(got["e"], ["Aiden_skillE1_01.wav", "Aiden_skillE1-2_01.wav"])
        self.assertEqual(
            got["q"],
            ["Bihyung_PlaySkill1088200seq0_1_ja.wav", "Bihyung_PlaySkill1088200seq0_2_ja.wav", "Bihyung_PlaySkill1088210seq0_1_ja.wav"],
        )
        self.assertEqual(got["r"], ["jackie_skillR_1_ko.wav", "jackie_skillR_2_ko.wav", "jackie_skillR_3_ko.wav"])
        self.assertEqual(got["select"][0], "magnus_selected_en.wav")
        self.assertEqual(len(got["select"]), 3)
        self.assertNotIn("w", got)
        self.assertNotIn("die", got)

    def test_select_filled_with_first_move(self) -> None:
        got = pick(["x_firstMove_2.wav", "x_selected_1.wav", "x_firstMove_1.wav", "x_skillQ_1.wav"])
        self.assertEqual(got["select"], ["x_selected_1.wav", "x_firstMove_1.wav", "x_firstMove_2.wav"])

    def test_die_lines(self) -> None:
        # die > killedCommon > lost, 보스 대사는 빼요
        got = pick(["a_newboss_die_1.wav", "a_lost_1.wav", "a_killedCommon_1_01.wav", "a_die_2_ko.wav", "a_die_1_ko.wav"])
        self.assertEqual(got["die"], ["a_die_1_ko.wav", "a_die_2_ko.wav", "a_killedCommon_1_01.wav"])
        self.assertEqual(pick(["hart_lost_1_ko.wav"])["die"], ["hart_lost_1_ko.wav"])

    def test_old_use_skill_active(self) -> None:
        # 예전 실험체 (피오라 · 키아라 · 하트 …): useSkillActive1 = Q … 4 = R
        self.assertEqual(voice_key("fiora_useSkillActive1_1_ko.wav"), "q")
        self.assertEqual(voice_key("hart_useSkillActive3Seq2_1_ko.wav"), "e")
        self.assertEqual(voice_key("chiara_useSkillActive4Seq0_1_ko.wav"), "r")

    def test_combat_lines_when_few_skill_lines(self) -> None:
        # 스킬 대사가 모자라면 전투 대사로 채워요 (모든 스킬이 먼저 1개씩, 상대 이름 도발은 빼요)
        got = pick(
            [
                "shoichi_selected_ko.wav",
                "shoichi_taunt_Hyunwoo_ko.wav",
                "shoichi_taunt_1_ko.wav",
                "shoichi_targetOn_2_ko.wav",
                "shoichi_targetOn_1_ko.wav",
                "shoichi_killMonster_1_ko.wav",
                "shoichi_skillE_1_ko.wav",
            ]
        )
        self.assertEqual(got["e"], ["shoichi_skillE_1_ko.wav"])
        self.assertEqual(got["q"], ["shoichi_targetOn_1_ko.wav", "shoichi_taunt_1_ko.wav"])
        self.assertEqual(got["w"], ["shoichi_targetOn_2_ko.wav"])
        self.assertEqual(got["r"], ["shoichi_killMonster_1_ko.wav"])
        self.assertNotIn("shoichi_taunt_Hyunwoo_ko.wav", [n for v in got.values() for n in v])

    def test_language(self) -> None:
        self.assertEqual(zip_lang("Jackie_KOR.zip"), "kor")
        self.assertEqual(zip_lang("bERnice_KOR.zip"), "kor")
        self.assertEqual(zip_lang("ENG.zip"), "eng")
        self.assertEqual(zip_lang("Henry_Voice Line_KOR.zip"), "kor")
        self.assertEqual(zip_lang("Bihyung_JPN.zip"), "jpn")
        self.assertEqual(zip_lang("voice.zip", ["a_skillQ_1_ja.wav", "a_selected_ja.wav"]), "jpn")


if __name__ == "__main__":
    unittest.main()
