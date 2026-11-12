"""구로 한신 18평 화장실 비포/애프터 릴스 생성 (1080x1920, 30fps)."""
import subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
OUT = sys.argv[1] if len(sys.argv) > 1 else "guro_hanshin_reel.mp4"

def font(size):
    return ImageFont.truetype(FONT, size)

def load(name):
    im = ImageOps.exif_transpose(Image.open(f"assets/{name}.jpg")).convert("RGB")
    # 9:16로 채우도록 미리 1.25배 여유 있게 리사이즈
    scale = max(W / im.width, H / im.height) * 1.25
    return im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)

IMG = {k: load(k) for k in ("before", "after1", "after2")}

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def kenburns(img, p, z0, z1, cx0=0.5, cy0=0.5, cx1=0.5, cy1=0.5):
    """p: 0~1 진행도. z: 1=화면 꽉, 클수록 확대."""
    e = ease(p)
    z = z0 + (z1 - z0) * e
    cx = cx0 + (cx1 - cx0) * e
    cy = cy0 + (cy1 - cy0) * e
    # 이미지는 화면 꽉 채움 기준 1.25배로 로드됨 → z=1이면 전체(cover) 표시
    k = 1.25 / z
    vw, vh = W * k, H * k
    x = cx * img.width - vw / 2
    y = cy * img.height - vh / 2
    x = max(0, min(img.width - vw, x))
    y = max(0, min(img.height - vh, y))
    return img.crop((int(x), int(y), int(x + vw), int(y + vh))).resize((W, H), Image.BILINEAR)

def text_center(d, y, s, size, fill=(255, 255, 255), stroke=0, sfill=(0, 0, 0)):
    f = font(size)
    w = d.textlength(s, font=f)
    d.text(((W - w) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

def pill(d, cx, y, s, size, bg, fg):
    f = font(size)
    w = d.textlength(s, font=f)
    pad = size * 0.55
    d.rounded_rectangle((cx - w / 2 - pad, y, cx + w / 2 + pad, y + size * 1.55),
                        radius=size, fill=bg)
    d.text((cx - w / 2, y + size * 0.22), s, font=f, fill=fg)

def shade(frame, top=True, bottom=True):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(520):
        a = int(170 * (1 - i / 520) ** 1.6)
        if top: d.line([(0, i), (W, i)], fill=(0, 0, 0, a))
        if bottom: d.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, a))
    return Image.alpha_composite(frame.convert("RGBA"), ov)

def fade_in(t, start, dur=0.35):
    return ease((t - start) / dur)

def caption(frame, t, t0, lines, label=None, label_bg=(230, 60, 60)):
    """lines: [(text, size)] 하단 자막, label: 상단 배지"""
    fr = shade(frame)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if label:
        pill(d, W / 2, 190, label, 58, label_bg + (255,), (255, 255, 255, 255))
    y = H - 430
    for i, (s, size) in enumerate(lines):
        text_center(d, y, s, size, stroke=3)
        y += size * 1.35
    a = fade_in(t, t0)
    if a < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return Image.alpha_composite(fr, layer)

# ── 장면 정의 (시작, 끝) ──────────────────────────────
SCENES = [
    (0.0, 3.2),   # 0 BEFORE 훅
    (3.2, 7.4),   # 1 AFTER 1 전체
    (7.4, 11.4),  # 2 AFTER 2 조명/세면대
    (11.4, 14.4), # 3 비포/애프터 분할
    (14.4, 17.0), # 4 엔드카드
]
TOTAL = SCENES[-1][1]
XF = 0.3  # 크로스페이드

def scene(i, t):
    s, e = SCENES[i]
    p = (t - s) / (e - s)
    if i == 0:
        # 살짝 흔들리며 줌인 (구축 느낌)
        shake = math.sin(t * 40) * 0.004 if t < 0.5 else 0
        f = kenburns(IMG["before"], p, 1.0, 1.15, 0.5 + shake, 0.5, 0.5, 0.55)
        f = f.convert("RGBA")
        out = caption(f, t, s + 0.1,
                      [("오래된 구축 화장실", 64), ("이게 이렇게 바뀝니다", 76)],
                      label="BEFORE")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        text_center(d, 300, "구로 한신 18평", 54, fill=(255, 255, 255, 230), stroke=2)
        return Image.alpha_composite(out, layer)
    if i == 1:
        f = kenburns(IMG["after1"], p, 1.12, 1.0, 0.55, 0.45, 0.5, 0.5)
        return caption(f, t, s + 0.15,
                       [("욕조 철거 → 유리 샤워부스", 66), ("넓어진 건식 공간", 56)],
                       label="AFTER", label_bg=(30, 30, 30))
    if i == 2:
        f = kenburns(IMG["after2"], p, 1.05, 1.05, 0.5, 0.35, 0.5, 0.65)
        return caption(f, t, s + 0.15,
                       [("수납장 하부 간접조명", 64), ("벽걸이 세면대로 깔끔하게", 56)],
                       label="AFTER", label_bg=(30, 30, 30))
    if i == 3:
        top = kenburns(IMG["before"], p, 1.0, 1.06)
        bot = kenburns(IMG["after1"], p, 1.0, 1.06)
        hh = H // 2
        f = Image.new("RGB", (W, H))
        f.paste(top.crop((0, hh // 2, W, hh // 2 + hh)), (0, 0))
        f.paste(bot.crop((0, hh // 2, W, hh // 2 + hh)), (0, hh))
        f = f.convert("RGBA")
        d = ImageDraw.Draw(f)
        d.rectangle((0, hh - 4, W, hh + 4), fill=(255, 255, 255, 255))
        pill(d, 150, 60, "BEFORE", 44, (230, 60, 60, 255), (255, 255, 255, 255))
        pill(d, 150, hh + 40, "AFTER", 44, (30, 30, 30, 255), (255, 255, 255, 255))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        text_center(dl, H - 230, "같은 공간, 완전히 다른 집", 64, stroke=4)
        a = fade_in(t, s + 0.2)
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        return Image.alpha_composite(f, layer)
    # 엔드카드
    bg = IMG["after2"].copy()
    f = kenburns(bg, 0.5, 1.0, 1.0).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
    f = Image.alpha_composite(f, Image.new("RGBA", (W, H), (15, 15, 15, 170)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    text_center(d, 700, "구로 한신아파트 18평", 70)
    text_center(d, 800, "올리모델링", 110)
    d.line([(W / 2 - 80, 970), (W / 2 + 80, 970)], fill=(255, 255, 255, 200), width=3)
    text_center(d, 1010, "구축이라 포기하지 마세요", 50, fill=(230, 230, 230, 255))
    pill(d, W / 2, 1200, "상담은 DM · 프로필 링크", 48, (255, 255, 255, 255), (20, 20, 20, 255))
    text_center(d, 1340, "@design_jplus_official", 46, fill=(255, 255, 255, 235))
    a = fade_in(t, s + 0.1, 0.5)
    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return Image.alpha_composite(f, layer)

def frame_at(t):
    for i, (s, e) in enumerate(SCENES):
        if s <= t < e:
            cur = scene(i, t).convert("RGB")
            # 다음 장면으로 크로스페이드 (BEFORE→AFTER는 화이트 플래시)
            if i + 1 < len(SCENES) and t > e - XF:
                a = (t - (e - XF)) / XF
                if i == 0:
                    white = Image.new("RGB", (W, H), (255, 255, 255))
                    return Image.blend(cur, white, a)
                return Image.blend(cur, scene(i + 1, t).convert("RGB"), a)
            if i == 1 and t < s + 0.25:  # 플래시 빠지는 구간
                white = Image.new("RGB", (W, H), (255, 255, 255))
                return Image.blend(white, cur, (t - s) / 0.25)
            return cur
    return scene(len(SCENES) - 1, TOTAL - 1e-3).convert("RGB")

if __name__ == "__main__":
    n = int(TOTAL * FPS)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", OUT,
    ], stdin=subprocess.PIPE)
    for k in range(n):
        ff.stdin.write(frame_at(k / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    print("done", OUT)
