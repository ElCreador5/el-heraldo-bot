"""Render a Discord-native progress attachment resembling the compact level-up card.

This module is presentation-only: no member operations, database access,
external assets, fonts written to disk, or file-system dependencies.
Pillow is imported lazily so non-image bot paths continue to start on hosts
without image dependencies.
"""
from __future__ import annotations

from io import BytesIO


WIDTH = 960
HEIGHT = 286


def _font(size: int, *, bold: bool = False):
    from PIL import ImageFont
    preferred = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(preferred, size)
    except OSError:
        return ImageFont.load_default(size=size)


def _right(draw, right: int, top: int, value: str, *, font, color):
    bounds = draw.textbbox((0, 0), value, font=font)
    draw.text((right - (bounds[2] - bounds[0]), top), value, font=font, fill=color)


def render_sync_card(
    *,
    title: str,
    state: str,
    checked: int,
    total: int | None,
    added: int,
    removed: int,
    failed: int,
    labels: dict[str, str],
) -> bytes:
    """Return a small dark PNG with an estimated bar, or animated-style activity.

    Discord's member_count is approximate; a running job never displays 100%.
    If the count is missing/stale, show activity with no invented percent.
    """
    from PIL import Image, ImageDraw

    checked = max(0, int(checked))
    usable = (isinstance(total, int) and not isinstance(total, bool)
              and total > 0 and checked <= total)
    fraction = min(0.99, checked / total) if usable else None
    image = Image.new("RGB", (WIDTH, HEIGHT), "#252630")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, WIDTH - 2, HEIGHT - 2),
                           radius=27, fill="#23242C", outline="#343747", width=2)
    # Narrow violet accent echoes the server's interaction color.
    draw.rounded_rectangle((44, 31, 51, 54), radius=3, fill="#7785FF")
    draw.text((68, 27), title, font=_font(24, bold=True), fill="#BEC2D4")
    draw.text((46, 66), state, font=_font(43, bold=True), fill="#F5F6FD")

    if usable:
        amount = labels["count"].format(checked=checked, total=total)
        percent = f"{min(99, checked * 100 // total)}%"
        side_label = labels["estimated"]
    else:
        amount = labels["unknown_count"].format(checked=checked)
        percent = "···"
        side_label = labels["unknown"]

    draw.text((48, 139), amount, font=_font(25), fill="#BDC0CF")
    _right(draw, WIDTH - 48, 71, percent, font=_font(48, bold=True), color="#F6F6FB")
    _right(draw, WIDTH - 48, 142, side_label, font=_font(21), color="#AEB3C6")

    # Fine anti-aliased pill bar: gray track, solid violet-blue foreground.
    left, top, right, bottom = 48, 184, WIDTH - 48, 205
    draw.rounded_rectangle((left, top, right, bottom), radius=10, fill="#3C3E4C")
    length = right - left
    if fraction is None:
        block = round(length * 0.21)
        offset = (checked // 25 * 33) % max(1, length - block)
        start, end = left + offset, left + offset + block
    else:
        start, end = left, left + round(length * fraction)
    if end > start:
        draw.rounded_rectangle((start, top, end, bottom), radius=10, fill="#6875F7")

    # Three compact and legible counters below the bar.
    y = 235
    metrics = (
        (48, f"+{added}", labels["added"], "#9ABFAF"),
        (365, f"-{removed}", labels["removed"], "#BEC2D4"),
        (672, str(failed), labels["failed"], "#F7A9A8" if failed else "#BEC2D4"),
    )
    for x, value, caption, ink in metrics:
        draw.text((x, y), value, font=_font(26, bold=True), fill=ink)
        bounds = draw.textbbox((0, 0), value, font=_font(26, bold=True))
        draw.text((x + bounds[2] + 12, y + 3), caption,
                  font=_font(22), fill="#9FA5B8")
    for x in (335, 638):
        draw.line((x, 235, x, 258), fill="#434657", width=2)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
