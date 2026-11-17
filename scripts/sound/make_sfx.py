# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 효과음 만들기 — 코드로 합성하는 8비트 느낌 소리 (남의 소리 파일을 쓰지 않아서 저작권 걱정이 없어요)

11-18 SG: 공식 효과음이 없는 자리는 채우기로. 포켓로그 효과음은 원래 포켓몬 게임 소리라 안 써요 (assets/README.md).
팬키트 · 공식 음원에서 같은 자리 소리를 받으면 그 파일로 바꿔 끼우면 돼요 (그 자리는 SOUNDS 에서 빼요).

  python3 -I -B scripts/sound/make_sfx.py            → assets/audio/{ui,se,battle_anims}/*.wav 를 새로 써요
  python3 -I -B scripts/sound/make_sfx.py --list     → 만들 소리 목록만

모든 소리는 22050Hz · 모노 · 16비트 WAV. 무작위(잡음)도 씨앗을 고정해서 매번 같은 소리가 나와요.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "assets" / "audio"
SR = 22050


# ── 재료 ─────────────────────────────────────────────


def t_of(dur: float) -> np.ndarray:
    return np.arange(int(SR * dur)) / SR


def sweep(f0: float, f1: float, dur: float, curve: str = "exp") -> np.ndarray:
    """시간에 따라 바뀌는 주파수 (Hz 배열)"""
    x = np.linspace(0, 1, int(SR * dur), endpoint=False)
    if curve == "exp" and f0 > 0 and f1 > 0:
        return f0 * (f1 / f0) ** x
    return f0 + (f1 - f0) * x


def osc(freq, dur: float, kind: str = "square", duty: float = 0.5) -> np.ndarray:
    n = int(SR * dur)
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq)[:n]
    phase = np.cumsum(f) / SR % 1.0
    if kind == "square":
        return np.where(phase < duty, 1.0, -1.0)
    if kind == "triangle":
        return 4 * np.abs(phase - 0.5) - 1
    if kind == "saw":
        return 2 * phase - 1
    return np.sin(2 * np.pi * phase)


def noise(dur: float, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).uniform(-1, 1, int(SR * dur))


def lowpass(x: np.ndarray, cutoff) -> np.ndarray:
    """한 극 저역 통과 (cutoff 는 숫자나 배열)"""
    if np.isscalar(cutoff):
        c = np.full(len(x), float(cutoff))
    else:
        c = np.asarray(cutoff, dtype=float)
        if len(c) != len(x):  # 길이가 조금 달라도 늘리거나 줄여 맞춰요
            c = np.interp(np.linspace(0, 1, len(x)), np.linspace(0, 1, len(c)), c)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x: np.ndarray, cutoff) -> np.ndarray:
    return x - lowpass(x, cutoff)


def env(n_or_x, a: float = 0.005, d: float = 0.0, s: float = 1.0, r: float = 0.05, curve: float = 1.0) -> np.ndarray:
    """ADSR 모양 (길이는 소리 길이와 같게)"""
    n = n_or_x if isinstance(n_or_x, int) else len(n_or_x)
    e = np.full(n, s)
    na, nd, nr = int(SR * a), int(SR * d), int(SR * r)
    na, nd, nr = min(na, n), min(nd, max(0, n - na)), min(nr, n)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nd:
        e[na : na + nd] = np.linspace(1, s, nd)
    if nr:
        e[n - nr :] *= np.linspace(1, 0, nr) ** curve
    return e


def decay(n_or_x, k: float = 8.0) -> np.ndarray:
    """처음 크게 → 빨리 작아짐 (k 가 클수록 빨리)"""
    n = n_or_x if isinstance(n_or_x, int) else len(n_or_x)
    e = np.exp(-k * np.arange(n) / SR)
    e[: min(n, 40)] *= np.linspace(0, 1, min(n, 40))
    return e


def tone(freq, dur, kind="square", duty=0.5, a=0.003, r=0.03, vol=1.0) -> np.ndarray:
    x = osc(freq, dur, kind, duty)
    return x * env(x, a=a, r=r) * vol


def bell(freq: float, dur: float, vol: float = 1.0, k: float = 6.0) -> np.ndarray:
    """종 · 반짝이 (사인 + 배음)"""
    t = t_of(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t)
    return x * decay(x, k) * vol / 1.65


def seq(*parts, gap: float = 0.0) -> np.ndarray:
    g = np.zeros(int(SR * gap))
    out = []
    for i, p in enumerate(parts):
        out.append(p)
        if gap and i < len(parts) - 1:
            out.append(g)
    return np.concatenate(out)


def mix(*parts) -> np.ndarray:
    """(소리, 시작 초) 들을 겹쳐요. 소리만 주면 0초에서 시작"""
    items = [(p, 0.0) if isinstance(p, np.ndarray) else p for p in parts]
    n = max(int(SR * at) + len(x) for x, at in items)
    out = np.zeros(n)
    for x, at in items:
        s = int(SR * at)
        out[s : s + len(x)] += x
    return out


def echo(x: np.ndarray, delay: float = 0.09, fb: float = 0.35, taps: int = 3) -> np.ndarray:
    return mix(x, *[(x * fb**k, delay * k) for k in range(1, taps + 1)])


def note(name: str) -> float:
    """음 이름 → Hz (예: C6, G#5)"""
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    key, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[key] + 12 * (octave - 4)) / 12)


def arp(notes: str, step: float, kind="square", duty=0.5, last: float | None = None, vol=1.0) -> np.ndarray:
    ns = notes.split()
    parts = [tone(note(n), (last if (last and i == len(ns) - 1) else step), kind, duty, r=0.02, vol=vol) for i, n in enumerate(ns)]
    return seq(*parts)


# ── 소리 목록: (폴더, 이름, 어디서 나오나, 만드는 함수) ──────────────

SOUNDS: list[tuple[str, str, str, callable]] = []


def sound(folder: str, name: str, where: str):
    def deco(fn):
        SOUNDS.append((folder, name, where, fn))
        return fn

    return deco


# 버튼 · 메뉴
@sound("ui", "select", "버튼 · 칸 고르기 (커서 움직이기 · 결정)")
def _():
    return seq(tone(note("C6"), 0.03, duty=0.25), tone(note("G6"), 0.04, duty=0.25)) * 0.5


@sound("ui", "menu_open", "메뉴 · 창 열기")
def _():
    return arp("G5 C6 E6", 0.03, "triangle", last=0.07) * 0.6


@sound("ui", "error", "안 되는 칸을 눌렀을 때")
def _():
    a = mix(tone(196, 0.09, duty=0.5), tone(185, 0.09, duty=0.5))
    return seq(a, a, gap=0.03) * 0.35


# 전투: 맞기 · 쓰러짐
@sound("se", "hit", "스킬에 맞을 때 (보통)")
def _():
    body = osc(sweep(150, 60, 0.12), 0.12, "sine") * decay(int(SR * 0.12), 25)
    crack = lowpass(noise(0.07, 2), 3500) * decay(int(SR * 0.07), 45)
    return mix(body * 0.9, crack * 0.8)


@sound("se", "hit_strong", "스킬에 크게 맞을 때 (효과가 굉장할 때)")
def _():
    body = osc(sweep(130, 40, 0.22), 0.22, "sine") * decay(int(SR * 0.22), 14)
    crack = lowpass(noise(0.16, 3), 5000) * decay(int(SR * 0.16), 22)
    click = tone(1800, 0.012, "square") * 0.4
    return mix(body, crack * 0.9, click)


@sound("se", "hit_weak", "스킬에 약하게 맞을 때 (효과가 별로일 때)")
def _():
    body = osc(sweep(120, 70, 0.08), 0.08, "sine") * decay(int(SR * 0.08), 35)
    soft = lowpass(noise(0.05, 4), 1500) * decay(int(SR * 0.05), 60)
    return mix(body * 0.6, soft * 0.4)


@sound("se", "faint", "실험체가 쓰러질 때")
def _():
    f = sweep(700, 70, 0.7) * (1 + 0.03 * np.sin(2 * np.pi * 18 * t_of(0.7)))
    x = osc(f, 0.7, "square", 0.4) * env(int(SR * 0.7), a=0.01, r=0.3)
    return lowpass(x, 2500) * 0.45


@sound("se", "flee", "도망칠 때")
def _():
    n = noise(0.38, 5)
    cut = np.concatenate([np.linspace(400, 4000, int(SR * 0.19)), np.linspace(4000, 600, int(SR * 0.19))])
    return lowpass(highpass(n, 200), cut[: len(n)]) * env(n, a=0.05, r=0.15) * 0.8


# 성장
@sound("se", "exp", "경험치 막대가 찰 때")
def _():
    x = osc(sweep(330, 1320, 0.6), 0.6, "triangle") * env(int(SR * 0.6), a=0.01, r=0.08)
    return x * 0.4


@sound("se", "level_up", "레벨이 오를 때 (짧게)")
def _():
    return echo(arp("C6 E6 G6 C7", 0.055, "square", 0.5, last=0.12), 0.07, 0.3, 2) * 0.35


@sound("se", "level_up_fanfare", "레벨업 · 새 실험체 해금 · 레벨 제한 풀림 (팡파르)")
def _():
    lead = seq(
        tone(note("G5"), 0.11, duty=0.5), tone(note("G5"), 0.11, duty=0.5), tone(note("G5"), 0.11, duty=0.5),
        tone(note("C6"), 0.33, duty=0.5, r=0.08), tone(note("A#5"), 0.16, duty=0.5), tone(note("C6"), 0.16, duty=0.5),
        tone(note("E6"), 0.55, duty=0.5, r=0.3),
    )
    bass = seq(tone(note("C4"), 0.33, "triangle"), tone(note("C4"), 0.33, "triangle"), tone(note("F4"), 0.32, "triangle"), tone(note("C4"), 0.55, "triangle", r=0.3))
    return mix(lead * 0.3, bass * 0.45)


@sound("se", "item_fanfare", "아이템 · 보상을 받을 때 (팡파르)")
def _():
    lead = seq(tone(note("E6"), 0.12, duty=0.25), tone(note("G6"), 0.12, duty=0.25), tone(note("C7"), 0.5, duty=0.25, r=0.3))
    harm = seq(tone(note("C5"), 0.24, "triangle"), tone(note("E5"), 0.5, "triangle", r=0.3))
    return mix(lead * 0.3, harm * 0.4, (bell(note("C7") * 2, 0.5, 0.25), 0.24))


@sound("se", "stat_up", "능력이 오를 때")
def _():
    one = osc(sweep(400, 1000, 0.12), 0.12, "square", 0.25) * env(int(SR * 0.12), a=0.005, r=0.03)
    return seq(one, one * 0.8, one * 0.6, gap=0.02) * 0.35


@sound("se", "stat_down", "능력이 내려갈 때")
def _():
    one = osc(sweep(1000, 350, 0.14), 0.14, "square", 0.25) * env(int(SR * 0.14), a=0.005, r=0.03)
    return seq(one, one * 0.8, one * 0.6, gap=0.02) * 0.35


@sound("se", "restore", "회복 아이템 · 체력 회복")
def _():
    notes = ["C6", "E6", "G6", "C7", "E7"]
    return mix(*[(bell(note(n), 0.5, 0.45, 7), i * 0.07) for i, n in enumerate(notes)]) * 0.7


@sound("se", "low_hp", "체력이 적을 때 경고음 (불러 두기만 하고 지금 게임에서 틀지는 않아요)")
def _():
    beep = tone(note("A5"), 0.09, "square", 0.5, r=0.02)
    return seq(beep, beep, gap=0.07) * 0.3


# 반짝 · 빛
@sound("se", "sparkle", "반짝일 때 (색다른 실험체 · 시작 화면 반짝)")
def _():
    rng = np.random.default_rng(7)
    return mix(*[(bell(float(rng.uniform(2000, 3600)), 0.25, 0.4, 14), i * 0.05) for i in range(6)]) * 0.6


@sound("se", "shine", "진화 · 모습이 바뀔 때 빛")
def _():
    gl = osc(sweep(800, 2400, 0.5), 0.5, "sine") * env(int(SR * 0.5), a=0.05, r=0.2)
    return mix(gl * 0.4, (bell(note("C7"), 0.6, 0.5, 5), 0.3))


@sound("se", "shing", "반짝이는 짧은 쇳소리 (잠재력 · 사탕 막대)")
def _():
    return bell(1850, 0.45, 0.8, 9) * 0.7


@sound("se", "charge", "진화 · 모습 바뀌기 전에 힘 모으기")
def _():
    f = sweep(90, 900, 0.9)
    x = osc(f, 0.9, "saw") * env(int(SR * 0.9), a=0.1, r=0.1)
    return lowpass(x, 3000) * 0.3


@sound("se", "beam", "진화 · 모습 바뀌는 순간 (빛줄기)")
def _():
    z = osc(sweep(1400, 220, 0.32), 0.32, "saw") * decay(int(SR * 0.32), 6)
    return mix(lowpass(z, 4000) * 0.5, lowpass(noise(0.2, 8), 6000) * decay(int(SR * 0.2), 15) * 0.3)


@sound("se", "upgrade", "보상 등급이 오를 때 · 상점 칸 잠금 풀기")
def _():
    return seq(tone(note("E6"), 0.07, duty=0.25), tone(note("B6"), 0.18, duty=0.25, r=0.12)) * 0.4


@sound("se", "buy", "상점에서 살 때 · 크레딧 쓸 때")
def _():
    return seq(tone(note("B5"), 0.06, duty=0.5), tone(note("E6"), 0.25, duty=0.5, r=0.2)) * 0.35


@sound("se", "achv", "업적 달성")
def _():
    return mix(arp("G5 C6 E6 G6", 0.07, "triangle", last=0.3) * 0.5, (bell(note("G6") * 2, 0.6, 0.3, 5), 0.21))


# 영입 볼 (판 중 영입)
@sound("se", "pb_throw", "영입 볼을 던질 때")
def _():
    n = noise(0.25, 9)
    return lowpass(highpass(n, 400), np.linspace(1500, 5000, len(n))) * env(n, a=0.02, r=0.1) * 0.5


@sound("se", "pb_rel", "볼이 열릴 때 · 실험체가 나올 때 · 보상 칸이 나올 때")
def _():
    pop = osc(sweep(900, 250, 0.08), 0.08, "sine") * decay(int(SR * 0.08), 30)
    return mix(pop * 0.8, lowpass(noise(0.03, 10), 6000) * decay(int(SR * 0.03), 90) * 0.4)


@sound("se", "pb_bounce_1", "볼이 튈 때 · 보상 칸 뒤집기 (높은 톡)")
def _():
    return osc(sweep(1600, 900, 0.04), 0.04, "sine") * decay(int(SR * 0.04), 60) * 0.7


@sound("se", "pb_bounce_2", "볼이 튈 때 (낮은 톡)")
def _():
    return osc(sweep(1100, 600, 0.04), 0.04, "sine") * decay(int(SR * 0.04), 60) * 0.6


@sound("se", "pb_move", "볼이 흔들릴 때 · 보급 상자 흔들림")
def _():
    c = lowpass(noise(0.03, 11), 3000) * decay(int(SR * 0.03), 80)
    return mix(c * 0.6, (c * 0.4, 0.06))


@sound("se", "pb_catch", "영입 성공 (딸깍 + 종)")
def _():
    click = mix(lowpass(noise(0.02, 12), 5000) * 0.6, tone(2200, 0.01, duty=0.5) * 0.3)
    return mix(click, (arp("C6 G6", 0.08, "triangle", last=0.35) * 0.4, 0.06))


@sound("se", "pb_lock", "볼이 잠길 때 (딸깍딸깍)")
def _():
    c = lowpass(noise(0.015, 13), 6000) * decay(int(SR * 0.015), 120)
    return mix(c * 0.7, (c * 0.5, 0.07))


@sound("se", "crit_throw", "영입 볼이 크게 날아갈 때 (확정 던지기)")
def _():
    rng = np.random.default_rng(14)
    return mix(*[(bell(float(rng.uniform(2400, 3800)), 0.18, 0.4, 18), i * 0.035) for i in range(5)]) * 0.6


@sound("se", "pb_tray_enter", "전투 시작 때 남은 볼 줄이 들어올 때")
def _():
    t = lowpass(noise(0.02, 15), 4000) * decay(int(SR * 0.02), 120)
    return mix(*[(t * 0.4, i * 0.05) for i in range(6)])


@sound("se", "pb_tray_ball", "볼 줄에 볼 하나 (있음)")
def _():
    return osc(1300, 0.03, "sine") * decay(int(SR * 0.03), 80) * 0.5


@sound("se", "pb_tray_empty", "볼 줄에 빈칸 하나")
def _():
    return osc(500, 0.03, "sine") * decay(int(SR * 0.03), 80) * 0.4


# 보급 상자 (알 · 뽑기 자리)
@sound("se", "egg_crack", "보급 상자에 금이 갈 때")
def _():
    n = highpass(noise(0.08, 16), 1200)
    return n * decay(n, 50) * 0.7


@sound("se", "egg_hatch", "보급 상자가 열릴 때")
def _():
    pop = osc(sweep(300, 1200, 0.12), 0.12, "square", 0.3) * env(int(SR * 0.12), r=0.05)
    return mix(pop * 0.3, (arp("C6 E6 G6 C7", 0.06, "triangle", last=0.4) * 0.45, 0.1))


@sound("se", "gacha_dial", "보급 요청 손잡이 돌리기")
def _():
    t = lowpass(noise(0.012, 17), 5000) * decay(int(SR * 0.012), 150)
    return mix(*[(t * 0.5, i * 0.045) for i in range(7)])


@sound("se", "gacha_running", "보급 요청 기계가 돌아갈 때")
def _():
    hum = lowpass(osc(55, 1.2, "saw"), 400) * env(int(SR * 1.2), a=0.1, r=0.2) * 0.25
    t = lowpass(noise(0.012, 18), 4000) * decay(int(SR * 0.012), 150)
    return mix(hum, *[(t * 0.35, 0.05 + i * 0.09) for i in range(12)])


@sound("se", "gacha_dispense", "보급 상자가 나올 때 (쿵 + 톡)")
def _():
    thunk = osc(sweep(160, 60, 0.12), 0.12, "sine") * decay(int(SR * 0.12), 25)
    return mix(thunk * 0.8, (osc(sweep(900, 400, 0.05), 0.05, "sine") * decay(int(SR * 0.05), 50) * 0.5, 0.1))


# 실험체 스킬 연출 7종 (battle_anims, make_fx.py 의 연출에서 틀어요)
@sound("battle_anims", "bseo-slash.wav", "스킬 연출: 베기 (칼 · 도끼 · 창 무기)")
def _():
    n = noise(0.2, 19)
    swish = highpass(n, np.linspace(800, 3000, len(n))) * env(n, a=0.03, r=0.12)
    return mix(swish * 0.7, (bell(2600, 0.25, 0.25, 16), 0.06))


@sound("battle_anims", "bseo-strike.wav", "스킬 연출: 타격 (망치 · 글러브 · 방망이 무기)")
def _():
    body = osc(sweep(180, 50, 0.16), 0.16, "sine") * decay(int(SR * 0.16), 20)
    crunch = lowpass(noise(0.1, 20), 2500) * decay(int(SR * 0.1), 35)
    return mix(body, crunch * 0.7)


@sound("battle_anims", "bseo-shot.wav", "스킬 연출: 투사체 (총 · 활 · 던지기 · 아르카나 등)")
def _():
    pew = osc(sweep(1500, 280, 0.14), 0.14, "square", 0.3) * decay(int(SR * 0.14), 14)
    return mix(pew * 0.45, lowpass(noise(0.05, 21), 5000) * decay(int(SR * 0.05), 60) * 0.3)


@sound("battle_anims", "bseo-blast.wav", "스킬 연출: 폭발 (위력 100 넘는 궁극기 R)")
def _():
    n = noise(1.0, 22)
    boom = lowpass(n, np.linspace(2500, 200, len(n))) * decay(n, 3.5)
    rumble = osc(sweep(80, 35, 1.0), 1.0, "sine") * decay(int(SR * 1.0), 3)
    return mix(boom * 1.0, rumble * 0.6)


@sound("battle_anims", "bseo-heal.wav", "스킬 연출: 회복 (체력 회복 변화 스킬)")
def _():
    notes = ["G5", "C6", "E6", "G6"]
    return mix(*[(bell(note(n), 0.45, 0.4, 7), i * 0.08) for i, n in enumerate(notes)]) * 0.7


@sound("battle_anims", "bseo-buff.wav", "스킬 연출: 강화 (자기 능력 올리는 변화 스킬)")
def _():
    x = osc(sweep(300, 1200, 0.45), 0.45, "triangle") * env(int(SR * 0.45), a=0.02, r=0.1)
    shimmer = osc(sweep(600, 2400, 0.45), 0.45, "square", 0.2) * env(int(SR * 0.45), a=0.05, r=0.15) * 0.15
    return mix(x * 0.45, shimmer)


@sound("battle_anims", "bseo-debuff.wav", "스킬 연출: 약화 (상대에게 거는 변화 스킬)")
def _():
    f = sweep(900, 220, 0.5) * (1 + 0.06 * np.sin(2 * np.pi * 12 * t_of(0.5)))
    x = osc(f, 0.5, "square", 0.35) * env(int(SR * 0.5), a=0.01, r=0.15)
    return lowpass(x, 2200) * 0.4


# ── 저장 ────────────────────────────────────────────


def finish(x: np.ndarray, peak: float = 0.85) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    x = x - np.mean(x)
    m = np.max(np.abs(x)) or 1.0
    # 소리마다 크기를 맞추되 원래 작게 만든 소리는 작게 (0.35 보다 큰 것만 줄여요)
    scale = min(1.0, peak / m) if m > peak else 1.0
    x = x * scale
    fade = min(len(x), int(SR * 0.004))
    x[-fade:] *= np.linspace(1, 0, fade)
    return x


def write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def file_of(folder: str, name: str) -> Path:
    return AUDIO / folder / (name if name.endswith(".wav") else f"{name}.wav")


def main() -> None:
    if "--list" in sys.argv:
        for folder, name, where, _ in SOUNDS:
            print(f"{folder}/{name}\t{where}")
        return
    done = []
    for folder, name, where, fn in SOUNDS:
        x = finish(fn())
        path = file_of(folder, name)
        write_wav(path, x)
        done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))
        print(f"{folder}/{name:22s} {len(x) / SR:5.2f}s  {where}")
    # 임시(무음) 파일 목록에서 빼요 (scripts/placeholder-assets/make.py 가 덮어쓰지 않게)
    mark = ROOT / "assets" / ".placeholders.json"
    if mark.exists():
        marks = set(json.loads(mark.read_text(encoding="utf-8")))
        before = len(marks)
        marks -= set(done)
        mark.write_text(json.dumps(sorted(marks), ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"임시 소리 목록에서 뺀 것: {before - len(marks)}개")


if __name__ == "__main__":
    main()
