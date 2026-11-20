#!/usr/bin/env python3
"""Render the 20 November 2026 world news as a 1024x1024 black-and-white
newspaper front page. Run `python3 draw.py` and it writes entry.png next
to this file. Pillow is the only dependency.

Layout, top to bottom: masthead, dateline, lead story (ICJ / Rohingya),
two-column row (Shenzhen summit, Kyiv war), three-column row (Riyadh,
markets, GTA 6), then a black ticker strip with the rest of the day.
Every text block is wrapped to its box and the script aborts instead of
letting a line spill out of its frame, so a bad fit is caught here rather
than in the shipped image.
"""
import os

from PIL import Image, ImageDraw, ImageFont

PAGE = 1024
EDGE = 36
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FAINT = (96, 96, 96)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
TICKER_LEADING = 22  # pixel step between ticker lines; strip fits 4 lines
SERIF = os.path.join(FONT_DIR, "DejaVuSerif.ttf")
SERIF_BOLD = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def load(path, size):
    return ImageFont.truetype(path, size)


def split_lines(canvas, text, face, width):
    """Greedy wrap of `text` into lines no wider than `width` pixels."""
    out, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if canvas.textlength(trial, font=face) <= width:
            current = trial
        else:
            if current:
                out.append(current)
            current = word
    if current:
        out.append(current)
    return out


class Page:
    """A 1024x1024 white sheet with helpers for newspaper blocks."""

    def __init__(self):
        self.image = Image.new("RGB", (PAGE, PAGE), WHITE)
        self.canvas = ImageDraw.Draw(self.image)
        self.left = EDGE
        self.right = PAGE - EDGE
        self.span = self.right - self.left

    def hline(self, y, weight=2):
        self.canvas.line([(self.left, y), (self.right, y)], fill=BLACK, width=weight)

    def vline(self, x, y0, y1):
        self.canvas.line([(x, y0), (x, y1)], fill=FAINT, width=1)

    def put_lines(self, lines, x, y, face, gap=None, colour=BLACK):
        step = gap if gap is not None else int(face.size * 1.28)
        for line in lines:
            self.canvas.text((x, y), line, font=face, fill=colour)
            y += step
        return y

    def headline(self, text, width, size, most_lines):
        """Biggest bold serif headline that fits `most_lines` lines."""
        size_now = size
        while size_now > 20:
            face = load(SERIF_BOLD, size_now)
            lines = split_lines(self.canvas, text, face, width)
            if len(lines) <= most_lines:
                return face, lines
            size_now -= 2
        face = load(SERIF_BOLD, 20)
        return face, split_lines(self.canvas, text, face, width)[:most_lines]

    def card(self, x, y, width, tag, title, body, title_size=30,
             title_lines=3, body_size=19, body_cap=6):
        """Kicker + headline + body block. Returns the y below the block
        and raises SystemExit if the body cannot fit its line budget."""
        self.canvas.text((x, y), tag, font=load(SANS_BOLD, 16), fill=BLACK)
        y += 26
        face, lines = self.headline(title, width, title_size, title_lines)
        y = self.put_lines(lines, x, y, face, gap=int(face.size * 1.18))
        y += 6
        body_face = load(SANS, body_size)
        body_lines = split_lines(self.canvas, body, body_face, width)
        if len(body_lines) > body_cap:
            raise SystemExit(
                f"OVERFLOW in '{tag}': {len(body_lines)} body lines > {body_cap}")
        return self.put_lines(body_lines, x, y, body_face,
                              gap=int(body_size * 1.32))

    def masthead(self):
        face = load(SERIF_BOLD, 92)
        name = "THE WORLD"
        wide = self.canvas.textlength(name, font=face)
        self.canvas.text(((PAGE - wide) / 2, 18), name, font=face, fill=BLACK)
        self.hline(138, 4)
        self.hline(144, 1)
        date_face = load(SANS_BOLD, 21)
        dateline = "FRIDAY 20 NOVEMBER 2026  \u2022  WORLD NEWS IN ONE PAGE"
        wide = self.canvas.textlength(dateline, font=date_face)
        self.canvas.text(((PAGE - wide) / 2, 156), dateline, font=date_face, fill=BLACK)
        self.hline(190, 2)

    def lead(self, y):
        self.canvas.text((self.left, y), "THE HAGUE  \u2022  WORLD COURT  \u2022  LEAD STORY",
                         font=load(SANS_BOLD, 17), fill=BLACK)
        y += 28
        face, lines = self.headline(
            "World court rules Myanmar committed genocide against the Rohingya",
            self.span, 42, 2)
        y = self.put_lines(lines, self.left, y, face, gap=int(face.size * 1.15))
        y += 6
        summary = (
            "In a first for the world court, the International Court of Justice "
            "found Myanmar responsible for genocide against the Rohingya, and "
            "ordered restitution and a full investigation.")
        body_face = load(SANS, 20)
        body_lines = split_lines(self.canvas, summary, body_face, self.span)
        if len(body_lines) > 3:
            raise SystemExit(f"lead overflow: {len(body_lines)} lines")
        y = self.put_lines(body_lines, self.left, y, body_face, gap=26)
        y += 8
        facts = "9\u20136 VOTE   \u2022   ABOUT 10,000 KILLED   \u2022   RESTITUTION ORDERED"
        self.canvas.text((self.left, y), facts, font=load(SANS_BOLD, 19), fill=BLACK)
        y += 30
        self.hline(y, 3)
        return y + 14

    def ticker(self, y):
        top = y
        height = PAGE - 24 - top
        self.canvas.rectangle([self.left, top, self.right, top + height], fill=BLACK)
        face = load(SANS_BOLD, 16)
        items = (
            "COP31 draft drops fossil-fuel phase-out  \u2022  Kenya discharges last "
            "Ebola patient, 37 days after first case  \u2022  EU\u2013UK summit  \u2022  "
            "Estonia to close Russia border for 6 months  \u2022  Poland: Russia "
            "violated airspace with 3 objects  \u2022  Bukele registers for third "
            "term  \u2022  Migrant boat capsizes off Senegal  \u2022  Trump: no Iran "
            "decision until new year; Senate blocks war-powers measure 51\u201348")
        lines = split_lines(self.canvas, items, face, self.span - 28)
        if len(lines) > 4:
            raise SystemExit(f"ticker overflow: {len(lines)} lines")
        ty = top + (height - len(lines) * TICKER_LEADING) // 2
        for line in lines:
            self.canvas.text((self.left + 14, ty), line, font=face, fill=WHITE)
            ty += TICKER_LEADING

    def save(self):
        here = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(here, "entry.png")
        self.image.save(target, "PNG", optimize=True)
        print(f"wrote {target}  {PAGE}x{PAGE}  {os.path.getsize(target)} bytes")


STORIES_ROW1 = [
    dict(tag="SHENZHEN  \u2022  SUMMIT",
         title="Trump, Xi and Putin meet in first trilateral summit",
         body=("The leaders issued a four-point Declaration toward Peace: UN "
               "reform, more refined-fuel supply, limits on ICC jurisdiction "
               "over state officials, and a nuclear-risk dialogue with no date "
               "set. Ukraine and Iran were not mentioned. Trump called it "
               "\u201cbigger than Yalta\u201d; Germany\u2019s Merz called it "
               "\u201cabove all a photo op\u201d."),
         title_size=28, body_size=17, body_cap=6),
    dict(tag="KYIV  \u2022  WAR IN UKRAINE",
         title="Russia hits Kyiv bridges; Ukraine strikes Crimea Bridge again",
         body=("Overnight strikes on bridges in Kyiv killed 8 people and injured "
               "28 across nine regions. Ukraine hit the Crimea Bridge for a "
               "third time this week, and President Putin vowed a response."),
         title_size=28, body_size=17, body_cap=6),
]

STORIES_ROW2 = [
    dict(tag="RIYADH  \u2022  MISSILE",
         title="Houthi missile damages Saudi wealth-fund tower",
         body=("A Houthi missile damaged the Public Investment Fund tower in "
               "Riyadh\u2019s financial district."),
         title_size=24, body_size=16, body_cap=4),
    dict(tag="MARKETS  \u2022  STOCKS",
         title="Anthropic soars on debut as markets slide",
         body=("Anthropic closed near $97 on debut, up 17% on its $83 offer. "
               "The S&P 500 fell about 2%, its fifth straight loss; the Nikkei "
               "dropped 4.8%."),
         title_size=24, body_size=16, body_cap=4),
    dict(tag="GAMING  \u2022  GTA 6",
         title="GTA 6 launch tops $2.3 billion in sales",
         body=("Grand Theft Auto VI passed $2.3 billion in sales, one of the "
               "biggest entertainment launches ever reported."),
         title_size=24, body_size=16, body_cap=4),
]


def build():
    sheet = Page()
    sheet.masthead()
    y = sheet.lead(206)

    # Two wide stories side by side, split by a faint vertical rule.
    gap = 28
    wide = (sheet.span - gap) // 2
    row_y = y
    bottoms = []
    for i, story in enumerate(STORIES_ROW1):
        x = sheet.left + i * (wide + gap)
        bottoms.append(sheet.card(x, row_y, wide, story["tag"], story["title"],
                                  story["body"], title_size=story["title_size"],
                                  body_size=story["body_size"],
                                  body_cap=story["body_cap"]))
    y = max(bottoms) + 10
    sheet.hline(y, 2)
    sheet.vline(sheet.left + wide + gap // 2, row_y, y - 10)
    y += 12

    # Three narrower stories in a row.
    gap3 = 24
    narrow = (sheet.span - 2 * gap3) // 3
    row_y = y
    bottoms = []
    for i, story in enumerate(STORIES_ROW2):
        x = sheet.left + i * (narrow + gap3)
        bottoms.append(sheet.card(x, row_y, narrow, story["tag"], story["title"],
                                  story["body"], title_size=story["title_size"],
                                  body_size=story["body_size"],
                                  body_cap=story["body_cap"]))
    y = max(bottoms) + 12
    for i in (1, 2):
        sheet.vline(sheet.left + i * (narrow + gap3) - gap3 // 2, row_y, y - 12)
    sheet.hline(y, 2)
    sheet.ticker(y + 10)
    sheet.save()


if __name__ == "__main__":
    build()
