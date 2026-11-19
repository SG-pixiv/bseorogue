# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
AI 도트 밑그림 한꺼번에 정리 + 자동 검사 + 후보 표 (11-20 SG "91명돌리고 ... 검수도 확실히")

AI 그림 폴더 모양 (ComfyUI output/bseo/c00):
  <ER번호 3자리>_<이름>/<자세>_00001_.png      자세 = fa~fe (앞모습 적 팀) · ba~be (뒷모습 내 편)
  다시 뽑은 것은 <자세>_s<씨앗>_00001_.png

쓰는 법:
  python3 scripts/er-dot/review_batch.py <AI 그림 폴더> <나올 폴더> [--only 001_jackie,...] [--jobs 8]
  → <나올 폴더>/dot/<ER>_<이름>/<자세>.png   정리된 도트 (앞 80×80 · 뒤 80×120)
  → <나올 폴더>/sheet/<ER>_<이름>.png        실험체마다 후보 표 (위 앞 5 · 아래 뒤 5, 검사에 걸린 것은 빨간 글씨)
  → <나올 폴더>/report.json                   자세마다 검사 결과

자동 검사 (걸리면 표에 빨간 글씨):
  크기 · 반투명 · 15색 · 키(앞 70~76px) · 발끝(앞 맨 아래 1px 위) · 머리 위 여유(뒤 4px) · 아래 잘림(뒤 맨 아래 줄까지)
  배경 남음(초록 · 분홍 점) · 바깥 외곽선(어두운 색 60% 이상) · 조각(떨어진 큰 덩어리 2개 이상) · 얼굴(머리 안 어두운 점 2개 이상, 앞만)
  · 너무 작음 / 너무 큼(칸 대비 채운 넓이)
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clean_dot  # noqa: E402

FRONT, BACK = (80, 80), clean_dot.BACK
POSES = ["fa", "fb", "fc", "fd", "fe", "ba", "bb", "bc", "bd", "be"]


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def clean(src: Path, dst: Path, back: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-I", "-B", str(HERE / "clean_dot.py"), str(src), str(dst)] + (["--back"] if back else ["--size", "L"])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return "" if r.returncode == 0 and dst.exists() else (r.stderr.strip().splitlines() or ["정리 실패"])[-1]


def components(mask: list[list[bool]]) -> list[int]:
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    sizes = []
    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0][x0] or seen[y0][x0]:
                continue
            stack, n = [(x0, y0)], 0
            seen[y0][x0] = True
            while stack:
                x, y = stack.pop()
                n += 1
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            sizes.append(n)
    return sorted(sizes, reverse=True)


def check(path: Path, back: bool) -> list[str]:
    """걸린 것들 (한국어 짧게). 빈 목록이면 통과"""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    flags = []
    want = BACK if back else FRONT
    if im.size != want:
        return [f"크기 {w}×{h}"]
    px = im.load()
    alphas = {px[x, y][3] for y in range(h) for x in range(w)}
    if alphas - {0, 255}:
        flags.append("반투명")
    colors = {px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3]}
    if len(colors) > 15:
        flags.append(f"색 {len(colors)}개")
    mask = [[px[x, y][3] > 0 for x in range(w)] for y in range(h)]
    box = im.getchannel("A").getbbox()
    if not box:
        return ["빈 그림"]
    x0, y0, x1, y1 = box
    area = sum(map(sum, mask))
    fill = area / (w * h)
    if fill < (0.12 if not back else 0.25):
        flags.append("너무 작음")
    if fill > (0.55 if not back else 0.8):
        flags.append("너무 큼")
    if back:
        if y1 != h:
            flags.append("아래 안 잘림")
        if y0 < clean_dot.BACK_TOP - 1:
            flags.append("머리 위 여유 없음")
    else:
        tall = y1 - y0
        if not 70 <= tall <= 76:
            flags.append(f"키 {tall}px")
        if y1 != h - 1:
            flags.append("발끝 자리")
    # 배경 남음: 아주 쨍한 초록 · 분홍
    bgish = sum(1 for c in colors if (c[1] > 200 and c[0] < 90 and c[2] < 90) or (c[0] > 200 and c[2] > 200 and c[1] < 90))
    if bgish:
        flags.append("배경 남음")
    # 바깥 외곽선: 실루엣 가장자리 칸 중 어두운 색 비율
    edge = [(x, y) for y in range(h) for x in range(w) if mask[y][x]
            and any(not (0 <= x + dx < w and 0 <= y + dy < h) or not mask[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            and not (back and y == h - 1)]
    dark_edge = sum(1 for x, y in edge if clean_dot.luma(px[x, y]) < clean_dot.DARK_LUMA)
    if edge and dark_edge / len(edge) < 0.6:
        flags.append(f"외곽선 {round(100 * dark_edge / len(edge))}%")
    sizes = components(mask)
    if len(sizes) > 1 and sizes[1] > 0.15 * sizes[0]:
        flags.append("조각 여러 개")
    if not back:
        # 얼굴: 머리 부분(위 22%) 안쪽(외곽선 아닌 칸)에 어두운 점이 2개 이상
        head_rows = range(y0, y0 + round((y1 - y0) * clean_dot.FACE_TOP))
        edge_set = set(edge)
        inner_dark = sum(1 for y in head_rows for x in range(w) if mask[y][x] and (x, y) not in edge_set
                         and clean_dot.luma(px[x, y]) < 110
                         and sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if clean_dot.luma(px[x + dx, y + dy]) > 150) >= 2)
        if inner_dark < 2:
            flags.append("얼굴 흐림")
    return flags


def font(size: int):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "C:/Windows/Fonts/malgun.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    found = sorted(Path("/usr/share/fonts").rglob("*CJK*.tt*")) if Path("/usr/share/fonts").exists() else []
    return ImageFont.truetype(str(found[0]), size) if found else ImageFont.load_default()


def sheet(name: str, ai_dir: Path, dot_dir: Path, report: dict, out: Path) -> None:
    """위: 앞 5 (AI 그림 작게 + 도트 3배) · 아래: 뒤 5"""
    f, fs = font(18), font(14)
    cw, chf, chb = 250, 210, 290
    canvas = Image.new("RGB", (cw * 5, 34 + chf + chb), (246, 246, 246))
    d = ImageDraw.Draw(canvas)
    d.text((8, 6), name, fill=(20, 20, 20), font=f)
    for i, pose in enumerate(POSES):
        back = pose[0] == "b"
        col, top = i % 5, 34 + (chf if back else 0)
        x = col * cw
        dot = dot_dir / f"{pose}.png"
        ai = ai_dir / f"{pose}_00001_.png"
        if ai.exists():
            a = Image.open(ai).convert("RGB")
            a.thumbnail((80, 160 if back else 110))
            canvas.paste(a, (x + 4, top + 24))
        if dot.exists():
            z = Image.open(dot).convert("RGBA")
            bg = Image.new("RGBA", z.size, (84, 104, 132, 255))
            bg.alpha_composite(z)
            canvas.paste(bg.convert("RGB").resize((z.width * 2, z.height * 2), Image.NEAREST), (x + 88, top + 24))
        flags = report.get(pose)
        label = pose + (" ✓" if flags == [] else "")
        d.text((x + 4, top + 2), label, fill=(30, 120, 30) if flags == [] else (20, 20, 20), font=fs)
        if flags:
            d.text((x + 4, top + (chb if back else chf) - 22), " · ".join(flags)[:30], fill=(200, 30, 30), font=fs)
    canvas.save(out)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    only = set(arg("--only", "").split(",")) - {""}
    chars = sorted(p for p in src.iterdir() if p.is_dir() and (not only or p.name in only))
    jobs = []
    for c in chars:
        for pose in POSES:
            ai = c / f"{pose}_00001_.png"
            if ai.exists():
                jobs.append((c.name, pose, ai))
    (dst / "dot").mkdir(parents=True, exist_ok=True)
    (dst / "sheet").mkdir(parents=True, exist_ok=True)
    rep_path = dst / "report.json"
    report = json.loads(rep_path.read_text(encoding="utf-8")) if rep_path.exists() else {}

    def run(job):
        name, pose, ai = job
        out = dst / "dot" / name / f"{pose}.png"
        if not out.exists() or out.stat().st_mtime < ai.stat().st_mtime:
            err = clean(ai, out, pose[0] == "b")
            if err:
                return name, pose, [f"정리 실패: {err[:40]}"]
        return name, pose, check(out, pose[0] == "b")

    with ThreadPoolExecutor(arg("--jobs", 8)) as ex:
        for name, pose, flags in ex.map(run, jobs):
            report.setdefault(name, {})[pose] = flags
    for c in chars:
        if c.name in report:
            sheet(c.name, c, dst / "dot" / c.name, report[c.name], dst / "sheet" / f"{c.name}.png")
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for r in report.values() for v in r.values() if v == [])
    total = sum(len(r) for r in report.values())
    print(f"{len(chars)}명 · {total}장 정리, 검사 통과 {ok}장 → {dst}")


if __name__ == "__main__":
    main()
