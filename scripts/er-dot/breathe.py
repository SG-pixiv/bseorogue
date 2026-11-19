# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
숨쉬기 움직임 만들기: 정리된 도트 한 장 → 2~4장 (11-19 SG "숨쉬기만 2~4장")

AI 로 장마다 그리면 모양이 조금씩 달라져서, 한 장에서 허리 위를 1px 내렸다 올리는 식으로 자동으로 만들어요.
  2장: [그대로, 허리 위 1px 아래로]
  3장: [그대로, 어깨 위 1px 아래로, 허리 위 1px 아래로]
  4장: [그대로, 어깨 위 1px 아래로, 허리 위 1px 아래로, 어깨 위 1px 아래로]  ← 0 → 1 → 2 → 1 → (처음으로)
허리 · 어깨 높이는 캐릭터 키(투명 아닌 맨 위 ~ 맨 아래)에서 비율로 잡아요 (--waist 0.45, --shoulder 0.25, 위에서부터).
발은 안 움직여서 땅에 붙어 있어요. 무기 · 팔이 허리 아래로 내려온 캐릭터는 손 보정에서 확인해요.

쓰는 법:
  python3 scripts/er-dot/breathe.py <정리된 도트.png> <나올 이름.png> [--frames 2|3|4] [--waist 0.45] [--shoulder 0.25]
  → <나올 이름.png>: 프레임을 옆으로 이어 붙인 띠 (80×80 이면 4장일 때 320×80)
  → <나올 이름>-zoom4.gif: 4배 확대 미리보기 (한 장 0.25초)
"""
import sys

from PIL import Image


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def body_rows(im: Image.Image) -> tuple[int, int]:
    box = im.getchannel("A").getbbox()
    if not box:
        raise ValueError("빈 그림이에요")
    return box[1], box[3]  # 맨 위 줄, 맨 아래 줄 + 1


def shift_upper(im: Image.Image, split: int) -> Image.Image:
    """split 줄보다 위를 1px 아래로. 맨 위 줄은 비고, split 줄은 위 부분의 마지막 줄로 덮여요"""
    out = im.copy()
    w = im.width
    upper = im.crop((0, 0, w, split))
    out.paste(Image.new("RGBA", (w, split + 1), (0, 0, 0, 0)), (0, 0))
    out.paste(im.crop((0, split + 1, w, im.height)), (0, split + 1))
    out.alpha_composite(upper, (0, 1))
    # 위 부분 마지막 줄(split-1 → split)이 비어 있는 칸은 원래 split 줄을 그대로 둬요 (몸 아래쪽이 끊기지 않게)
    px, src = out.load(), im.load()
    for x in range(w):
        if px[x, split][3] == 0 and src[x, split][3]:
            px[x, split] = src[x, split]
    return out


def frames(im: Image.Image, n: int, waist: float, shoulder: float) -> list[Image.Image]:
    top, bottom = body_rows(im)
    h = bottom - top
    w_row = top + round(h * waist)
    s_row = top + round(h * shoulder)
    a = shift_upper(im, s_row)
    b = shift_upper(im, w_row)
    return {2: [im, b], 3: [im, a, b], 4: [im, a, b, a]}[n]


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    n = arg("--frames", 4)
    if n not in (2, 3, 4):
        sys.exit("--frames 는 2 · 3 · 4 중 하나예요")
    im = Image.open(src).convert("RGBA")
    fs = frames(im, n, arg("--waist", 0.45), arg("--shoulder", 0.25))
    strip = Image.new("RGBA", (im.width * n, im.height), (0, 0, 0, 0))
    for i, f in enumerate(fs):
        strip.paste(f, (i * im.width, 0))
    strip.save(dst)
    gif = dst.rsplit(".", 1)[0] + "-zoom4.gif"
    big = []
    for f in fs:
        bg = Image.new("RGBA", f.size, (84, 104, 132, 255))
        bg.alpha_composite(f)
        big.append(bg.convert("RGB").resize((f.width * 4, f.height * 4), Image.NEAREST))
    big[0].save(gif, save_all=True, append_images=big[1:], duration=250, loop=0)
    print(f"{dst}: {n}장 ({strip.width}×{strip.height}), 미리보기 {gif}")


if __name__ == "__main__":
    main()
