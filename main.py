#!/usr/bin/env python3
"""Draw the front page of THE WORLD TODAY for Sunday 22 November 2026.

Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (``/output``
when the variable is unset). The page sums up six stories that happened
or were first reported on Sunday 22 November 2026:

  1. Iran says it struck US defences in Bahrain -- the IRGC claims a
     combined missile and drone operation against two US Patriot air
     defence radars; Bahrain investigates a Patriot interceptor crash.
  2. Mexico captures FBI most-wanted cartel boss Fausto Isidro Meza
     Flores, known as El Chapo Isidro, in a Sinaloa raid; deadly
     violence follows, 11 killed.
  3. The EU and Indonesia sign a landmark trade deal after ten years
     of talks, scrapping 98.5% of tariffs between them.
  4. The COP31 climate talks in Antalya stay deadlocked over fossil
     fuels and run deep into overtime past their Friday deadline.
  5. Drones hit a Russian cargo ship in the Baltic Sea; the vessel,
     bound for Kaliningrad, catches fire and the crew evacuates as
     Finland tightens security.
  6. TikTok launches a global deepfake-detection tool for public
     figures, ahead of a wave of European elections next year.

Everything is drawn in code: a plain RGB canvas, a bitmap font defined
below by hand (5x7 glyphs, no font file, no image file, no network),
simple geometric illustrations per story, and a hand-written PNG
encoder. Standard library only. No randomness, no timestamps, no
network: two runs produce byte-identical output.
"""

import hashlib
import math
import os
import struct
import zlib

W, H = 1024, 1024
MAX_FILE_SIZE = 1024 * 1024  # 1 MiB

PAPER = (248, 244, 232)
INK = (26, 26, 26)
MUTED = (96, 90, 78)
RED = (163, 22, 33)
PANEL = (255, 255, 255)
EDGE = (198, 192, 176)
SKY = (205, 228, 240)
NAVY = (18, 30, 58)
SLATE = (70, 90, 120)
GOLD = (212, 175, 55)
EUBLUE = (0, 51, 153)
GREEN = (46, 125, 50)
TAN = (210, 180, 140)
DARK = (16, 24, 48)
ORANGE = (232, 120, 30)
YELLOW = (245, 200, 60)
LIGHTBLUE = (170, 205, 235)
BROWN = (120, 85, 50)
GREY = (140, 140, 140)
TEAL = (0, 130, 130)
DESERT = (222, 196, 150)


class Canvas:
    """A plain RGB canvas backed by one bytearray per row."""

    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.rows = [bytearray(bg * width) for _ in range(height)]
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, width, height

    def clip_to(self, x, y, w, h):
        self.cx0, self.cy0 = max(0, x), max(0, y)
        self.cx1, self.cy1 = min(self.w, x + w), min(self.h, y + h)

    def unclip(self):
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, self.w, self.h

    def set_pixel(self, x, y, color):
        if self.cx0 <= x < self.cx1 and self.cy0 <= y < self.cy1:
            row = self.rows[y]
            row[x * 3] = color[0]
            row[x * 3 + 1] = color[1]
            row[x * 3 + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(self.cx0, x)
        y0 = max(self.cy0, y)
        x1 = min(self.cx1, x + w)
        y1 = min(self.cy1, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        fill = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            row = self.rows[yy]
            row[x0 * 3:x1 * 3] = fill

    def rect(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = thick // 2
        while True:
            self.fill_rect(x0 - r, y0 - r, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            half = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - half, yy, half * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5)
            inner2 = (r - thick) * (r - thick) - dy * dy
            inner = int(inner2 ** 0.5) if inner2 > 0 else 0
            self.fill_rect(cx - outer, yy, outer - inner, 1, color)
            self.fill_rect(cx + inner + 1, yy, outer - inner, 1, color)

    def triangle(self, p0, p1, p2, color):
        (x0, y0), (x1, y1), (x2, y2) = sorted(
            (p0, p1, p2), key=lambda p: p[1])
        if y2 == y0:
            return
        for yy in range(max(y0, self.cy0), min(y2 + 1, self.cy1)):
            if yy < y1:
                t = (yy - y0) / (y1 - y0) if y1 != y0 else 0.0
                xa = x0 + (x1 - x0) * t
                xb = x0 + (x2 - x0) * ((yy - y0) / (y2 - y0))
            else:
                t = (yy - y1) / (y2 - y1) if y2 != y1 else 0.0
                xa = x1 + (x2 - x1) * t
                xb = x0 + (x2 - x0) * ((yy - y0) / (y2 - y0))
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(lo, yy, hi - lo + 1, 1, color)


# ---------------------------------------------------------------------------
# Bitmap font: 5x7 glyphs defined by hand in this file. '#' is ink, '.' is
# blank. Only upper-case letters, digits and the punctuation the page uses.
# ---------------------------------------------------------------------------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}

CHAR_W = 5
CHAR_H = 7
CHAR_ADV = 6  # glyph width + 1px gap, before scaling


def text_width(text, scale):
    return len(text) * CHAR_ADV * scale - scale


def draw_text(canvas, x, y, text, scale, color):
    """Draw text with its top-left corner at (x, y). Text is upper-case."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += CHAR_ADV * scale
            continue
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == '1':
                    canvas.fill_rect(
                        cx + col_i * scale, y + row_i * scale,
                        scale, scale, color)
        cx += CHAR_ADV * scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split(' ')
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Story pictograms. Each draws inside a box (x, y, w, h) with its own sky.
# ---------------------------------------------------------------------------

def pic_bahrain(c, x, y, w, h):
    """Night sky over Bahrain: Patriot radar dish, missile streaks, burst."""
    c.fill_rect(x, y, w, h, NAVY)
    for sx, sy in ((18, 14), (70, 28), (150, 10), (230, 24), (285, 12),
                   (40, 44), (200, 42), (260, 52), (110, 18)):
        c.fill_rect(x + sx, y + sy, 3, 3, (255, 255, 255))
    # Radar dish on a launcher, left side.
    dx, dy = x + 78, y + 108
    c.line(dx - 34, dy - 30, dx + 34, dy - 30, GREY, 4)
    c.line(dx, dy - 30, dx, dy + 8, GREY, 5)
    c.fill_rect(dx - 40, dy + 8, 80, 10, (60, 60, 60))
    c.disc(dx, dy - 52, 16, LIGHTBLUE)
    c.ring(dx, dy - 52, 16, (255, 255, 255), 2)
    # Missile streaks converging on a burst, right side.
    bx, by = x + w - 80, y + 52
    c.line(x + 30, y + 14, bx - 8, by - 6, (255, 255, 255), 3)
    c.line(x + 90, y + 8, bx - 4, by - 14, (255, 255, 255), 3)
    c.line(x + 150, y + 20, bx + 2, by + 2, (255, 255, 255), 3)
    for k in range(12):
        ang = math.radians(k * 30.0)
        c.line(bx, by, int(bx + math.cos(ang) * 44),
               int(by + math.sin(ang) * 44),
               ORANGE if k % 2 == 0 else YELLOW, 5)
    c.disc(bx, by, 17, YELLOW)
    c.disc(bx, by, 9, ORANGE)
    # Desert ground with a small skyline.
    c.fill_rect(x, y + h - 18, w, 18, DESERT)
    for bx2, bw, bh in ((150, 46, 26), (200, 38, 34), (242, 52, 22)):
        c.fill_rect(x + bx2, y + h - 18 - bh, bw, bh, (10, 16, 34))


def pic_cartel(c, x, y, w, h):
    """Handcuffs and a gold star badge on a dark wanted-poster ground."""
    c.fill_rect(x, y, w, h, (40, 34, 28))
    # Wanted-poster band.
    c.fill_rect(x + 14, y + 10, w - 28, 24, (232, 220, 180))
    draw_text(c, x + 26, y + 14, "WANTED", 2, RED)
    # Two handcuff rings joined by a chain.
    cy = y + 82
    for cx in (x + 92, x + w - 92):
        c.ring(cx, cy, 34, (200, 200, 200), 7)
        c.ring(cx, cy, 22, (120, 120, 120), 3)
    for lx in range(x + 122, x + w - 122, 14):
        c.disc(lx, cy, 5, (200, 200, 200))
    # Gold star badge below.
    bx, by = x + w // 2, y + h - 34
    star = []
    for k in range(10):
        ang = math.radians(k * 36 - 90)
        r = 26 if k % 2 == 0 else 11
        star.append((bx + int(r * math.cos(ang)),
                     by + int(r * math.sin(ang))))
    for i in range(10):
        c.triangle((bx, by), star[i], star[(i + 1) % 10], GOLD)
    c.disc(bx, by, 9, (255, 255, 255))


def pic_trade(c, x, y, w, h):
    """EU flag and Indonesian flag side by side, joined by a green check."""
    c.fill_rect(x, y, w, h, (232, 226, 208))
    fx, fy, fw, fh = x + 18, y + 30, 122, 76
    c.fill_rect(fx, fy, fw, fh, EUBLUE)
    c.rect(fx, fy, fw, fh, INK, 2)
    ccx, ccy = fx + fw // 2, fy + fh // 2
    for k in range(12):
        ang = math.radians(k * 30 - 90)
        c.disc(int(ccx + 30 * math.cos(ang)),
               int(ccy + 23 * math.sin(ang)), 4, YELLOW)
    ix, iy, iw, ih = x + w - 140, y + 30, 122, 76
    c.fill_rect(ix, iy, iw, ih // 2, RED)
    c.fill_rect(ix, iy + ih // 2, iw, ih // 2, (255, 255, 255))
    c.rect(ix, iy, iw, ih, INK, 2)
    # Green check between the flags.
    hx, hy = x + w // 2, y + h - 26
    c.disc(hx, hy, 17, GREEN)
    c.line(hx - 8, hy, hx - 2, hy + 7, (255, 255, 255), 4)
    c.line(hx - 2, hy + 7, hx + 9, hy - 8, (255, 255, 255), 4)


def pic_climate(c, x, y, w, h):
    """Globe with a hot sun and an overtime clock."""
    c.fill_rect(x, y, w, h, SKY)
    cx, cy = x + w // 2 - 26, y + h // 2 + 2
    sx, sy = x + w - 54, y + 24
    c.disc(sx, sy, 21, ORANGE)
    for k in range(8):
        ang = math.radians(k * 45.0)
        c.line(int(sx + math.cos(ang) * 25), int(sy + math.sin(ang) * 25),
               int(sx + math.cos(ang) * 35), int(sy + math.sin(ang) * 35),
               ORANGE, 4)
    c.disc(cx, cy, 56, (58, 130, 200))
    c.ring(cx, cy, 56, (30, 90, 160), 3)
    c.disc(cx - 24, cy - 16, 15, GREEN)
    c.disc(cx + 20, cy + 12, 19, GREEN)
    c.disc(cx - 2, cy + 28, 11, GREEN)
    # Small clock, hands past the deadline.
    kx, ky = x + 42, y + h - 40
    c.disc(kx, ky, 20, (255, 255, 255))
    c.ring(kx, ky, 20, INK, 3)
    c.line(kx, ky, kx, ky - 13, INK, 3)
    c.line(kx, ky, kx + 11, ky + 5, INK, 3)
    c.fill_rect(x, y + h - 16, w, 16, TAN)
    c.fill_rect(x, y + h - 16, w, 3, BROWN)


def pic_baltic(c, x, y, w, h):
    """Cargo ship on a grey sea, drone above, smoke and flames."""
    c.fill_rect(x, y, w, h, (196, 212, 224))
    # Drone quadcopter, top right (enlarged so it reads at a glance).
    qx, qy = x + w - 74, y + 30
    c.fill_rect(qx - 18, qy - 5, 36, 10, INK)
    c.fill_rect(qx - 32, qy - 10, 16, 4, INK)
    c.fill_rect(qx + 16, qy - 10, 16, 4, INK)
    c.fill_rect(qx - 4, qy + 5, 8, 10, INK)
    c.line(qx - 10, qy + 32, qx + 46, y + 80, (255, 255, 255), 3)
    # Ship hull with containers.
    hx0, hy = x + 24, y + h - 52
    c.fill_rect(hx0, hy, w - 48, 26, (40, 60, 90))
    c.fill_rect(hx0, hy - 22, 60, 22, RED)
    c.fill_rect(hx0 + 66, hy - 22, 60, 22, YELLOW)
    c.fill_rect(hx0 + 132, hy - 22, 60, 22, TEAL)
    c.fill_rect(hx0 + w - 96, hy - 44, 34, 44, (240, 240, 240))
    c.fill_rect(hx0 + w - 88, hy - 36, 18, 8, NAVY)
    # Flames and smoke from the midship hit.
    fx = hx0 + 130
    c.triangle((fx - 16, hy - 20), (fx, hy - 58), (fx + 16, hy - 20),
               ORANGE)
    c.triangle((fx - 8, hy - 20), (fx, hy - 44), (fx + 8, hy - 20),
               YELLOW)
    c.disc(fx - 18, hy - 66, 10, GREY)
    c.disc(fx + 4, hy - 78, 13, GREY)
    c.disc(fx + 22, hy - 62, 9, GREY)
    # Sea waves.
    for wy in range(y + h - 22, y + h - 4, 8):
        for wx in range(x + 8, x + w - 8, 34):
            c.line(wx, wy, wx + 16, wy, (255, 255, 255), 2)


def pic_tiktok(c, x, y, w, h):
    """Phone with a music note, shielded by a verification check."""
    c.fill_rect(x, y, w, h, (24, 24, 30))
    # Phone (shortened so the caption below it stays on the dark ground).
    px, py, pw, ph = x + 34, y + 14, 108, 104
    c.fill_rect(px, py, pw, ph, (255, 255, 255))
    c.rect(px, py, pw, ph, INK, 2)
    c.fill_rect(px, py, pw, 16, INK)
    # Music note on the screen.
    nx, ny = px + pw // 2 + 6, py + 58
    c.disc(nx - 16, ny + 12, 9, (0, 0, 0))
    c.fill_rect(nx - 8, ny - 34, 4, 46, (0, 0, 0))
    c.fill_rect(nx - 8, ny - 34, 26, 4, (0, 0, 0))
    c.disc(nx + 18, ny + 12, 9, (0, 0, 0))
    c.fill_rect(nx + 26, ny - 34, 4, 46, (0, 0, 0))
    c.disc(nx - 16, ny + 12, 9, (255, 0, 80))
    c.disc(nx + 18, ny + 12, 9, (0, 242, 234))
    # Shield with a check, right side.
    sx, sy = x + w - 96, y + 44
    shield = [(sx, sy), (sx + 64, sy), (sx + 64, sy + 44),
              (sx + 32, sy + 84), (sx, sy + 44)]
    for i in range(5):
        c.line(shield[i][0], shield[i][1],
               shield[(i + 1) % 5][0], shield[(i + 1) % 5][1], TEAL, 4)
    c.fill_rect(sx + 8, sy + 8, 48, 64, (0, 180, 180))
    c.line(sx + 16, sy + 40, sx + 28, sy + 52, (255, 255, 255), 5)
    c.line(sx + 28, sy + 52, sx + 50, sy + 24, (255, 255, 255), 5)
    draw_text(c, x + 16, y + 124, "REAL OR FAKE?", 2, (255, 255, 255))


# ---------------------------------------------------------------------------
# Panels and page layout
# ---------------------------------------------------------------------------

def draw_panel(canvas, x, y, w, h, kicker, kicker_color, title, caption,
               pic_fn, fact=""):
    canvas.fill_rect(x, y, w, h, PANEL)
    canvas.rect(x, y, w, h, EDGE, 2)
    canvas.fill_rect(x, y, w, 34, kicker_color)
    draw_text(canvas, x + 12, y + 8, kicker.upper(), 2, (255, 255, 255))
    pic_fn(canvas, x + 2, y + 36, w - 4, 146)
    ty = y + 194
    # The bitmap font holds upper-case glyphs only: normalise here so a
    # mixed-case story line can never render as scattered fragments.
    for line in wrap_text(title.upper(), w - 24, 3):
        draw_text(canvas, x + 12, ty, line, 3, INK)
        ty += 26
    ty += 6
    for line in wrap_text(caption.upper(), w - 24, 2):
        draw_text(canvas, x + 12, ty, line, 2, (52, 52, 52))
        ty += 17
    if fact:
        lines = wrap_text(fact.upper(), w - 24, 2)
        fy = y + h - 12 - 17 * len(lines)
        canvas.fill_rect(x + 12, fy - 10, w - 24, 2, EDGE)
        for line in lines:
            draw_text(canvas, x + 12, fy, line, 2, RED)
            fy += 17


# One verified key fact per story, set in red at the foot of its panel.
FACTS = [
    "BAHRAIN PROBES INTERCEPTOR CRASH",
    "11 KILLED AS VIOLENCE FLARES",
    "98.5% OF TARIFFS TO GO",
    "DEAL AT RISK AS TALKS DRAG ON",
    "CREW EVACUATES, SHIP ABLAZE",
    "AHEAD OF EUROPEAN ELECTIONS",
]


STORIES = [
    ("MIDDLE EAST", NAVY,
     "IRAN STRIKES US BASES IN BAHRAIN",
     "Tehran claims missiles and drones hit two US Patriot radars.",
     pic_bahrain),
    ("MEXICO", (90, 60, 30),
     "MEXICO CAPTURES EL CHAPO ISIDRO",
     "FBI most-wanted cartel boss seized in a Sinaloa raid.",
     pic_cartel),
    ("TRADE", (30, 110, 70),
     "EU AND INDONESIA SIGN TRADE DEAL",
     "Ten years of talks end in a pact scrapping 98.5% of tariffs.",
     pic_trade),
    ("CLIMATE", TEAL,
     "COP31 TALKS DEADLOCKED IN OVERTIME",
     "Climate summit in Antalya runs past deadline over fossil fuels.",
     pic_climate),
    ("BALTIC", SLATE,
     "DRONES HIT RUSSIAN SHIP IN BALTIC",
     "Cargo vessel bound for Kaliningrad attacked; Finland on alert.",
     pic_baltic),
    ("TECH", (24, 24, 30),
     "TIKTOK LAUNCHES DEEPFAKE DETECTOR",
     "Global tool helps public figures spot AI fakes before elections.",
     pic_tiktok),
]


def draw_page():
    c = Canvas(W, H, PAPER)
    c.rect(0, 0, W, H, INK, 4)
    # Masthead
    title = "THE WORLD TODAY"
    tw = text_width(title, 7)
    draw_text(c, (W - tw) // 2, 26, title, 7, INK)
    c.fill_rect(28, 92, W - 56, 4, RED)
    date = "SUNDAY 22 NOVEMBER 2026"
    dw = text_width(date, 3)
    draw_text(c, (W - dw) // 2, 106, date, 3, RED)
    sub = "SIX STORIES FROM AROUND THE WORLD - THE DAY IN ONE PAGE"
    sw = text_width(sub, 2)
    draw_text(c, (W - sw) // 2, 138, sub, 2, MUTED)
    c.fill_rect(28, 162, W - 56, 2, EDGE)
    # Story grid: 3 columns x 2 rows
    margin, gap = 16, 12
    pw = (W - 2 * margin - 2 * gap) // 3
    ph = 404
    for i, story in enumerate(STORIES):
        col, row = i % 3, i // 3
        px = margin + col * (pw + gap)
        py = 176 + row * (ph + gap)
        draw_panel(c, px, py, pw, ph, *story, fact=FACTS[i])
    # Footer
    foot = "SOURCES: AP, REUTERS, BBC, ANI, ONE TURN - 22 NOVEMBER 2026"
    fw = text_width(foot, 1)
    draw_text(c, (W - fw) // 2, 1006, foot, 1, MUTED)
    return c


# ---------------------------------------------------------------------------
# PNG encoding (hand-written, standard library only) and entry point
# ---------------------------------------------------------------------------

def png_bytes(canvas):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(row) for row in canvas.rows)
    comp = zlib.compress(raw, 6)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def validate_png(data):
    """Re-parse the PNG we just encoded; raise on any structural flaw."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    seen = []
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert zlib.crc32(typ + body) & 0xFFFFFFFF == crc, "bad CRC: %r" % typ
        seen.append(typ)
        if typ == b"IHDR":
            (w, h, depth, ctype) = struct.unpack(">IIBB", body[:10])
            assert (w, h) == (W, H), "bad dimensions"
            assert depth == 8 and ctype == 2, "bad colour type"
        pos += 12 + length
    assert seen[0] == b"IHDR" and seen[-1] == b"IEND", "missing chunks"
    assert len(data) <= MAX_FILE_SIZE, "file over 1 MiB"


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(draw_page())
    validate_png(data)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
