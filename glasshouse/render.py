from __future__ import annotations
from html import escape
from pathlib import Path
import hashlib, json, os, tempfile


def _halftone(card_id: str) -> str:
    digest = hashlib.sha256(card_id.encode()).digest()
    dots = []
    for y in range(8, 104, 8):
        for x in range(7, 273, 8):
            wave = digest[(x // 8 + y // 8) % len(digest)] / 255
            radius = .7 + 2.2 * max(0, wave - y / 145)
            if radius > .8:
                dots.append(f'<circle cx="{x}" cy="{y}" r="{radius:.1f}"/>')
    return '<svg class="texture" viewBox="0 0 280 112" aria-hidden="true"><g>' + "".join(dots) + '</g></svg>'


def render_report(report: dict, output_path: Path | str) -> Path:
    output = Path(output_path)
    cards = []
    for index, card in enumerate(report.get("cards", [])):
        cards.append(f'''<article class="card card-{index % 5}">
  {_halftone(str(card.get("id", index)))}
  <div class="copy"><p class="question">{escape(str(card.get("question", "")))}</p>
  <h2>{escape(str(card.get("headline", "")))}</h2>
  <p>{escape(str(card.get("body", "")))}</p></div>
</article>''')
    title = f"Glasshouse — {escape(str(report.get('period', 'Report')))}"
    summary = escape(json.dumps(report.get("summary", {}), sort_keys=True))
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--ink:#28231f;--orange:#ff6433;--paper:#f7f4ee;--peach:#ff9b73}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif}}
main{{max-width:1440px;margin:auto;padding:7vw 5vw}} header{{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin-bottom:2.6rem;border-bottom:2px solid var(--ink)}}
h1{{font-size:clamp(3rem,8vw,8rem);letter-spacing:-.07em;line-height:.76;margin:0 0 .2em;text-transform:lowercase}} .period{{font:700 1rem/1 monospace;margin-bottom:1rem}}
.grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));align-items:stretch}} .card{{min-height:365px;background:#fff;border:1.5px solid var(--orange);display:grid;grid-template-rows:43% 1fr;overflow:hidden;position:relative}}
.card:nth-child(5n+1){{transform:rotate(-.65deg) translateY(3px)}} .card:nth-child(5n+2){{transform:rotate(.25deg)}} .card:nth-child(5n+4){{transform:rotate(.45deg) translateY(-2px)}} .card:nth-child(n+6){{margin-top:-4px}}
.texture{{width:100%;height:100%;background:var(--orange);fill:#fff}} .card-1 .texture,.card-3 .texture{{background:var(--peach)}} .copy{{padding:1rem 1rem 1.4rem;border-top:1.5px solid var(--orange)}}
.question{{color:var(--orange);font-size:.72rem;font-weight:700;margin:0 0 .85rem}} h2{{font-size:1.22rem;line-height:1.08;margin:0 0 .75rem;letter-spacing:-.025em}} .copy>p:last-child{{font-size:.9rem;line-height:1.45;margin:0}}
footer{{margin-top:3rem;font:11px/1.5 monospace;border-top:1px solid;padding-top:1rem;word-break:break-word}}
@media (max-width: 1050px){{.grid{{grid-template-columns:repeat(3,1fr)}}}}
@media (max-width: 700px){{main{{padding:3rem 1rem}} header{{display:block}} .grid{{grid-template-columns:1fr}} .card{{min-height:330px;transform:none!important;margin:-1px 0 0!important}}}}
@media (prefers-reduced-motion:reduce){{.card{{transform:none!important}}}}
@media print{{main{{padding:.2in}} .card{{transform:none!important;break-inside:avoid}} footer{{display:none}}}}
</style></head><body><main><header><h1>glasshouse</h1><p class="period">{escape(str(report.get('period','')))}</p></header>
<section class="grid" aria-label="Your coding-agent activity cards">{"".join(cards)}</section>
<footer aria-label="Collection summary">LOCAL ONLY · {summary}</footer></main></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle: handle.write(html)
        os.replace(temporary, output)
    except Exception:
        try: os.unlink(temporary)
        except OSError: pass
        raise
    return output

