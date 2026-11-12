"""심플 버전 릴스: 자막 최소화, 부드러운 크로스페이드, 밝은 엔드카드 (12초)."""
import subprocess, sys
from PIL import Image, ImageDraw
from make_reel import W, H, FPS, IMG, font, kenburns, ease

OUT = sys.argv[1] if len(sys.argv) > 1 else "guro_hanshin_reel_simple.mp4"
INK = (34, 34, 34)
PAPER = (244, 242, 238)

SCENES = [  # (시작, 끝, 사진, 라벨)
    (0.0, 3.0, "before", "BEFORE"),
    (3.0, 6.5, "after1", "AFTER"),
    (6.5, 9.5, "after2", "AFTER"),
    (9.5, 12.0, None, None),  # 엔드카드
]
TOTAL = SCENES[-1][1]
XF = 0.5

def spaced(d, xy, s, size, fill, spacing=0.25, anchor_center=False):
    f = font(size)
    widths = [d.textlength(c, font=f) for c in s]
    total = sum(widths) + size * spacing * (len(s) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for c, w in zip(s, widths):
        d.text((x, y), c, font=f, fill=fill)
        x += w + size * spacing

def overlay(base, alpha, draw_fn):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    return Image.alpha_composite(base, layer)

def photo_scene(i, t):
    s, e, name, label = SCENES[i]
    p = (t - s) / (e - s)
    f = kenburns(IMG[name], p, 1.0, 1.06).convert("RGBA")
    # 하단만 아주 옅게 어둡게 (글씨 가독성)
    shade = Image.new("L", (1, H))
    for y in range(H):
        shade.putpixel((0, y), int(90 * max(0, (y - H * 0.6) / (H * 0.4))))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dark.putalpha(shade.resize((W, H)))
    f = Image.alpha_composite(f, dark)
    a = ease((t - s - 0.2) / 0.6)
    def draw(d):
        spaced(d, (80, H - 480), label, 44, (255, 255, 255, 255), spacing=0.35)
        d.line([(80, H - 410), (140, H - 410)], fill=(255, 255, 255, 200), width=2)
        d.text((80, H - 385), "구로 한신 18평", font=font(36), fill=(255, 255, 255, 220))
    return overlay(f, a, draw)

def end_scene(t):
    s = SCENES[-1][0]
    f = Image.new("RGBA", (W, H), PAPER + (255,))
    a = ease((t - s - 0.1) / 0.7)
    def draw(d):
        spaced(d, (W / 2, 820), "BEFORE  /  AFTER", 34, (120, 120, 120, 255), 0.3, True)
        f1 = font(64)
        s1 = "구로 한신 18평 올리모델링"
        d.text(((W - d.textlength(s1, font=f1)) / 2, 900), s1, font=f1, fill=INK + (255,))
        d.line([(W / 2 - 40, 1030), (W / 2 + 40, 1030)], fill=INK + (255,), width=2)
        f2 = font(38)
        s2 = "@design_jplus_official"
        d.text(((W - d.textlength(s2, font=f2)) / 2, 1070), s2, font=f2, fill=(90, 90, 90, 255))
    return overlay(f, a, draw)

def scene(i, t):
    return (end_scene(t) if SCENES[i][2] is None else photo_scene(i, t)).convert("RGB")

def frame_at(t):
    for i, (s, e, _, _) in enumerate(SCENES):
        if s <= t < e:
            cur = scene(i, t)
            if i + 1 < len(SCENES) and t > e - XF:
                return Image.blend(cur, scene(i + 1, t), ease((t - (e - XF)) / XF))
            return cur
    return scene(len(SCENES) - 1, TOTAL - 1e-3)

if __name__ == "__main__":
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", OUT,
    ], stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)):
        ff.stdin.write(frame_at(k / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    print("done", OUT)
