# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 임시 그림 만들기

포켓로그 그림(assets)은 라이선스가 없어서 쓸 수 없어요. 대신 같은 이름 · 같은 크기의
단색 임시 그림을 새로 그려서 게임이 그대로 돌아가게 해요. 진짜 그림(이터널 리턴 리소스,
SG 그림)이 생기면 같은 이름으로 덮어써요.

- 원본 PNG · WAV 는 절대 복사하지 않아요. 크기와 아틀라스 칸 위치만 읽어요.
- JSON 은 원본 REUSE.toml 에 AGPL-3.0 · CC0 로 적힌 것만 그대로 복사하고,
  나머지 아틀라스 JSON 은 칸 이름 · 위치만 담아 새로 써요.
- 소리는 아주 짧은 무음 WAV 로 채워요.

쓰는 법:
  git clone --filter=blob:none --no-checkout --depth 1 --branch beta https://github.com/pagefaultgames/pokerogue-assets.git <참고폴더>
  (참고폴더에서 필요한 폴더만 sparse-checkout)
  python3 scripts/placeholder-assets/make.py <참고폴더> assets
이미 있는 파일(진짜 그림)은 덮어쓰지 않아요. --force 를 붙이면 임시 그림만 다시 만들어요.
"""
import fnmatch
import hashlib
import json
import os
import struct
import sys
import tomllib
import wave

from PIL import Image, ImageDraw, ImageFont

REF = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
FORCE = "--force" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = os.path.join(OUT, ".placeholders.json")  # 임시 그림 목록 (진짜 그림과 구분)

# 이터널 리턴 느낌의 어두운 남색 바탕 + 하늘색 테두리
PANEL = (31, 36, 56, 235)
BORDER = (99, 214, 255, 255)
TEXT_SLOT = (43, 49, 80, 235)
TEXT_BORDER = (255, 229, 138, 255)
SOFT = [(86, 98, 140), (120, 92, 150), (70, 128, 140), (150, 110, 80), (90, 140, 96), (140, 84, 100), (96, 110, 170), (160, 140, 70)]
SKIP_DIRS = {".git", ".github"}
# 기술 연출(battle-anims)은 공용 연출 + 블서로그 공용 이펙트 5개(베기 · 타격 · 폭발 · 투사체 · 회복)에 쓸 것만
ANIM_KEEP = ("common-", "encounter-")
ANIM_MOVES = {"slash", "tackle", "explosion", "shadow-ball", "recover", "quick-attack", "swords-dance", "protect", "focus-energy", "struggle", "tail-whip"}

placeholders = set(json.load(open(MARK))) if os.path.exists(MARK) else set()
stats = {"png": 0, "json_copy": 0, "json_atlas": 0, "wav": 0, "kept": 0, "skipped": []}


def load_reuse():
    """REUSE.toml 에서 AGPL · CC0 로 적힌 경로 패턴을 모아요"""
    ok = []
    for root, dirs, files in os.walk(REF):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if "REUSE.toml" not in files:
            continue
        base = os.path.relpath(root, REF)
        base = "" if base == "." else base + "/"
        with open(os.path.join(root, "REUSE.toml"), "rb") as f:
            data = tomllib.load(f)
        for a in data.get("annotations", []):
            lic = a.get("SPDX-License-Identifier", "")
            if lic not in ("AGPL-3.0-only", "CC0-1.0"):
                continue
            paths = a.get("path", [])
            if isinstance(paths, str):
                paths = [paths]
            ok += [base + p for p in paths]
    return ok


OPEN_JSON = load_reuse()


def free_json(rel):
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat + "/*") for pat in OPEN_JSON)


def color_of(name, alpha=230):
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
    r, g, b = SOFT[h % len(SOFT)]
    return (r, g, b, alpha)


def can_write(rel):
    dst = os.path.join(OUT, rel)
    if os.path.exists(dst) and rel not in placeholders:
        stats["kept"] += 1
        return False  # 진짜 그림이 이미 있어요
    if os.path.exists(dst) and not FORCE:
        return False
    return True


def save(rel, writer):
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    writer(dst)
    placeholders.add(rel)


def frames_of(atlas):
    """아틀라스 JSON → [(이미지 이름, [(칸 이름, x, y, w, h)])] (아틀라스가 아니면 [])"""
    try:
        return _frames_of(atlas)
    except (KeyError, TypeError, AttributeError):
        return []


def _frames_of(atlas):
    out = []
    if isinstance(atlas, dict) and "textures" in atlas:
        for t in atlas["textures"]:
            out.append((t.get("image"), [(f["filename"], *[f["frame"][k] for k in ("x", "y", "w", "h")]) for f in t.get("frames", [])]))
    elif isinstance(atlas, dict) and isinstance(atlas.get("frames"), list):
        out.append((atlas.get("meta", {}).get("image"), [(f["filename"], *[f["frame"][k] for k in ("x", "y", "w", "h")]) for f in atlas["frames"]]))
    elif isinstance(atlas, dict) and isinstance(atlas.get("frames"), dict):
        out.append((atlas.get("meta", {}).get("image"), [(n, *[f["frame"][k] for k in ("x", "y", "w", "h")]) for n, f in atlas["frames"].items()]))
    return out


def rewrite_atlas(atlas):
    """칸 이름 · 위치만 남긴 새 아틀라스 JSON (원본 구조 형식은 같게)"""
    def frame(f):
        keep = {k: f[k] for k in ("filename", "rotated", "trimmed", "sourceSize", "spriteSourceSize", "frame") if k in f}
        keep.setdefault("rotated", False)
        return keep
    if "textures" in atlas:
        return {"textures": [{"image": t.get("image"), "format": t.get("format", "RGBA8888"), "size": t.get("size"), "scale": t.get("scale", 1),
                              "frames": [frame(f) for f in t.get("frames", [])]} for t in atlas["textures"]],
                "meta": {"app": "bseorogue placeholder", "version": "1"}}
    if isinstance(atlas.get("frames"), list):
        return {"frames": [frame(f) for f in atlas["frames"]], "meta": {"app": "bseorogue placeholder", "image": atlas.get("meta", {}).get("image"), "size": atlas.get("meta", {}).get("size"), "scale": atlas.get("meta", {}).get("scale", "1")}}
    return {"frames": {n: {k: f[k] for k in ("rotated", "trimmed", "sourceSize", "spriteSourceSize", "frame") if k in f} for n, f in atlas["frames"].items()},
            "meta": {"app": "bseorogue placeholder", "image": atlas.get("meta", {}).get("image"), "size": atlas.get("meta", {}).get("size"), "scale": atlas.get("meta", {}).get("scale", "1")}}


def draw_box(d, x, y, w, h, fill, border):
    if w <= 0 or h <= 0:
        return
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill)
    if w >= 3 and h >= 3:
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=border)


def make_png(rel, src, atlas_frames):
    with Image.open(src) as im:
        w, h = im.size
        alpha = im.convert("RGBA").getchannel("A") if im.mode in ("RGBA", "LA", "P") else None
        bbox = alpha.getbbox() if alpha else (0, 0, w, h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    name = rel.lower()
    text_slot = "text_images" in name
    if atlas_frames:
        for fname, x, y, fw, fh in atlas_frames:
            draw_box(d, x, y, fw, fh, TEXT_SLOT if text_slot else color_of(fname), TEXT_BORDER if text_slot else BORDER)
    elif "/arenas/" in name and name.endswith("_bg.png"):
        for yy in range(h):  # 하늘 → 땅 색으로 단순한 배경
            t = yy / max(1, h - 1)
            c = (int(40 + 60 * t), int(52 + 70 * t), int(92 + 20 * t), 255)
            d.line([(0, yy), (w, yy)], fill=c)
    elif "/arenas/" in name:
        if bbox:
            x0, y0, x1, y1 = bbox
            d.ellipse([x0, y0, x1 - 1, y1 - 1], fill=(70, 86, 120, 255), outline=BORDER)
    elif bbox:
        x0, y0, x1, y1 = bbox
        fill = TEXT_SLOT if text_slot else (PANEL if "/ui/" in name else color_of(rel, 200))
        if "/ui/" in name and w >= 320 and h >= 180:
            fill = PANEL[:3] + (255,)  # 화면 전체를 덮는 배경은 불투명 (뒤 화면이 비치면 글자가 겹쳐 보여요)
        draw_box(d, x0, y0, x1 - x0, y1 - y0, fill, TEXT_BORDER if text_slot else BORDER)
    save(rel, lambda dst: img.save(dst, optimize=True))
    stats["png"] += 1


def make_wav(rel):
    def write(dst):
        with wave.open(dst, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(8000)
            f.writeframes(struct.pack("B", 128) * 200)
    save(rel, write)
    stats["wav"] += 1


def make_m4a(rel):
    """무음 m4a (ffmpeg 가 있을 때만)"""
    import shutil
    import subprocess
    if not shutil.which("ffmpeg"):
        stats["skipped"].append(rel)
        return
    def write(dst):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", "-t", "0.05", "-c:a", "aac", "-b:a", "8k", dst], check=True)
    save(rel, write)
    stats["wav"] += 1


def make_item_count_font(rel_png, rel_xml, src_xml):
    """아이템 개수 숫자용 비트맵 글꼴 (갈무리로 새로 그려요)"""
    import re
    xml = open(src_xml, encoding="utf-8").read()
    ids = [int(m) for m in re.findall(r'<char id="(\d+)"', xml)]
    ttf = os.environ.get("GALMURI_TTF")
    font = ImageFont.truetype(ttf, 11) if ttf and os.path.exists(ttf) else ImageFont.load_default()
    cw, ch = 7, 9
    img = Image.new("RGBA", (cw * max(1, len(ids)), ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    chars = []
    for i, cid in enumerate(ids):
        d.text((i * cw, -2), chr(cid), font=font, fill=(255, 255, 255, 255))
        chars.append(f'    <char id="{cid}" x="{i * cw}" y="0" width="{cw}" height="{ch}" xoffset="0" yoffset="0" xadvance="{cw - 1}" page="0" chnl="15" />')
    face = os.path.basename(rel_png).rsplit(".", 1)[0]
    out = f'<?xml version="1.0"?>\n<font>\n  <info face="{face}" size="{ch}" />\n  <common lineHeight="{ch}" base="{ch - 1}" scaleW="{img.width}" scaleH="{ch}" pages="1" />\n  <pages>\n    <page id="0" file="{os.path.basename(rel_png)}" />\n  </pages>\n  <chars count="{len(ids)}">\n' + "\n".join(chars) + "\n  </chars>\n</font>\n"
    save(rel_png, lambda dst: img.save(dst))
    save(rel_xml, lambda dst: open(dst, "w", encoding="utf-8").write(out))


def main():
    atlases = {}
    for root, dirs, files in os.walk(REF):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".json"):
                p = os.path.join(root, fn)
                try:
                    data = json.load(open(p, encoding="utf-8"))
                except Exception:
                    continue
                for image, frames in frames_of(data):
                    if image:
                        atlases[os.path.normpath(os.path.join(root, image))] = frames

    for root, dirs, files in os.walk(REF):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            src = os.path.join(root, fn)
            rel = os.path.relpath(src, REF).replace(os.sep, "/")
            if rel.startswith(("LICENSES/", "test/")) or fn in ("REUSE.toml", "README.md", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "tsconfig.json", "vitest.config.ts", "lefthook.yml", ".editorconfig", ".gitignore", ".gitkeep"):
                continue
            ext = fn.rsplit(".", 1)[-1].lower()
            if rel.startswith("battle-anims/") and not (fn.startswith(ANIM_KEEP) or fn[:-5] in ANIM_MOVES):
                continue
            if rel.startswith("fonts/item-count"):
                if ext == "xml" and can_write(rel):
                    make_item_count_font(rel[:-3] + "png", rel, src)
                continue
            if ext == "json":
                if not can_write(rel):
                    continue
                if free_json(rel):
                    save(rel, lambda dst, s=src: open(dst, "wb").write(open(s, "rb").read()))
                    stats["json_copy"] += 1
                else:
                    try:
                        data = json.load(open(src, encoding="utf-8"))
                    except Exception:
                        stats["skipped"].append(rel)
                        continue
                    if frames_of(data):
                        save(rel, lambda dst, d=data: json.dump(rewrite_atlas(d), open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":")))
                        stats["json_atlas"] += 1
                    elif fn == "_masterlist.json":
                        save(rel, lambda dst: open(dst, "w").write("{}"))  # 색 바뀐 개체 목록: 블서로그는 없음
                        stats["json_atlas"] += 1
                    else:
                        stats["skipped"].append(rel)
            elif ext == "png":
                if can_write(rel):
                    make_png(rel, src, atlases.get(os.path.normpath(src)))
            elif ext == "wav":
                if can_write(rel):
                    make_wav(rel)
            elif ext == "m4a":
                if can_write(rel):
                    make_m4a(rel)
            else:
                stats["skipped"].append(rel)

    json.dump(sorted(placeholders), open(MARK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(json.dumps({k: (v if k != "skipped" else len(v)) for k, v in stats.items()}, ensure_ascii=False))
    if stats["skipped"]:
        print("건너뛴 파일 (라이선스 없음 · 처리 못 함):", ", ".join(stats["skipped"][:30]), "…" if len(stats["skipped"]) > 30 else "")


main()
