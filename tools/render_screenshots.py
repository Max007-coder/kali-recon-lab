#!/usr/bin/env python3
"""Render the captured recon output as terminal-style PNG evidence shots.

The text drawn is exactly what the tools printed into recon/raw/ - this is a
rendering of real output, not a fabricated screenshot.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "recon" / "raw"
OUT = ROOT / "screenshots"

BG = (11, 14, 19)
BAR = (17, 22, 31)
BORDER = (43, 53, 67)
TEXT = (201, 211, 224)
DIM = (93, 107, 128)
GREEN = (61, 220, 132)
AMBER = (232, 179, 94)

W, H = 1500, 950
PAD = 34
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]
BOLD_PATHS = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def load(paths, size):
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def lines_of(name):
    f = RAW / name
    if not f.exists():
        return [f"(missing: {name})"]
    # tabs would render as tofu boxes in a monospace font
    return [ANSI.sub("", ln.rstrip("\n")).replace("\t", "    ")
            for ln in f.read_text(errors="replace").splitlines()]


def wrap(text, cols):
    if not text:
        return [""]
    out = []
    while len(text) > cols:
        out.append(text[:cols])
        text = text[cols:]
    out.append(text)
    return out


def render(dest, title, blocks):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    mono, bold, small = load(FONT_PATHS, 16), load(BOLD_PATHS or FONT_PATHS, 16), load(FONT_PATHS, 13)
    cw = mono.getlength("M")
    cols = int((W - 2 * PAD - 18) / cw)

    # window chrome
    d.rectangle([0, 0, W, 46], fill=BAR)
    for i, col in enumerate([(232, 69, 94), (232, 179, 94), (61, 220, 132)]):
        d.ellipse([18 + i * 24, 17, 30 + i * 24, 29], fill=col)
    d.text((W / 2 - small.getlength(title) / 2, 14), title, font=small, fill=DIM)
    d.line([(0, 46), (W, 46)], fill=BORDER)

    y = 46 + 22
    for cmd, body in blocks:
        prompt = "$ " + cmd
        d.text((PAD, y), prompt, font=bold, fill=GREEN)
        y += 26
        avail = int((H - y - PAD) / 24)
        shown = 0
        for raw in body:
            for ln in wrap(raw, cols):
                if shown >= avail - 2:
                    break
                d.text((PAD + 18, y), ln, font=mono, fill=TEXT)
                y += 24
                shown += 1
            if shown >= avail - 2:
                break
        total = sum(len(wrap(r, cols)) for r in body)
        if total > shown:
            d.text((PAD + 18, y), f"... {total - shown} more lines (full output in recon/raw)", font=mono, fill=AMBER)
            y += 24
        y += 14

    d.rectangle([2, 2, W - 3, H - 3], outline=BORDER)
    OUT.mkdir(exist_ok=True)
    img.save(dest, "PNG")
    print(f"wrote {dest.relative_to(ROOT)}  ({dest.stat().st_size // 1024} KB)")


def main():
    whois = lines_of("01-whois.txt")
    whois = whois[:16]  # registry block; the legal boilerplate below it is noise here
    render(
        OUT / "01-whois-dns.png",
        "kali ~ whois + nslookup + dig  example.com",
        [
            ("whois example.com", whois),
            ("nslookup example.com", lines_of("02-nslookup.txt")),
            ("dig example.com +noall +answer", lines_of("03-dig.txt")),
        ],
    )
    render(
        OUT / "02-http-fingerprint.png",
        "kali ~ curl -I + whatweb  example.com",
        [
            ("curl -sS -D - -o /dev/null https://example.com", lines_of("04-curl-headers.txt")),
            ("whatweb -a 1 https://example.com", lines_of("05-whatweb.txt")),
        ],
    )
    render(
        OUT / "03-waf-dnsrecon.png",
        "kali ~ wafw00f + dnsrecon  example.com",
        [
            ("wafw00f https://example.com", lines_of("06-wafw00f.txt")[6:]),
            ("dnsrecon -d example.com -t std", [
                re.sub(r"^\S+\+0200 ", "", ln) for ln in lines_of("07-dnsrecon.txt")
            ]),
        ],
    )


if __name__ == "__main__":
    sys.exit(main())
