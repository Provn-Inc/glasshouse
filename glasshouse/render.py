from __future__ import annotations
from html import escape
from pathlib import Path
import base64, hashlib, json, os, tempfile


def _provn_logo_data_uri() -> str:
    logo = Path(__file__).with_name("assets") / "provn-logo.png"
    encoded = base64.b64encode(logo.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _halftone(card_id: str) -> str:
    digest = hashlib.sha256(card_id.encode()).digest()
    pattern_id = f"dots-{digest.hex()[:10]}"
    dots = []
    for y in range(8, 104, 8):
        for x in range(7, 273, 8):
            wave = digest[(x // 8 + y // 8) % len(digest)] / 255
            radius = .7 + 2.2 * max(0, wave - y / 145)
            if radius > .8:
                dots.append(f'<circle cx="{x}" cy="{y}" r="{radius:.1f}"/>')
    return (
        '<svg class="texture" width="100%" height="100%" aria-hidden="true">'
        f'<defs><pattern id="{pattern_id}" patternUnits="userSpaceOnUse" width="280" height="112">'
        + "".join(dots)
        + f'</pattern></defs><rect width="100%" height="100%" fill="url(#{pattern_id})"/></svg>'
    )


def render_report(report: dict, output_path: Path | str) -> Path:
    output = Path(output_path)
    provn_logo = _provn_logo_data_uri()
    cards = []
    for index, card in enumerate(report.get("cards", [])):
        card_id = escape(str(card.get("id", index)), quote=True)
        cards.append(f'''<article class="card card-{index % 5}" id="card-{card_id}" data-card-id="{card_id}" role="button" tabindex="0" aria-haspopup="dialog" aria-controls="card-dialog" aria-expanded="false" aria-label="Open details: {escape(str(card.get('headline', '')), quote=True)}">
  {_halftone(str(card.get("id", index)))}
  <div class="copy"><p class="question">{escape(str(card.get("question", "")))}</p>
  <h2>{escape(str(card.get("headline", "")))}</h2>
  <p class="summary">{escape(str(card.get("body", "")))}</p>
  <p class="detail" hidden>{escape(str(card.get("detail", card.get("body", ""))))}</p>
  <span class="read-more" aria-hidden="true">Read the full card <span>↗</span></span></div>
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
.grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));align-items:stretch}} .card{{min-height:365px;background:#fff;border:1.5px solid var(--orange);display:grid;grid-template-rows:43% 1fr;overflow:hidden;position:relative;cursor:pointer;transform-origin:50% 70%;transition:box-shadow .18s ease,translate .18s ease}}
.card:nth-child(5n+1){{transform:rotate(-.65deg) translateY(3px)}} .card:nth-child(5n+2){{transform:rotate(.25deg)}} .card:nth-child(5n+4){{transform:rotate(.45deg) translateY(-2px)}} .card:nth-child(n+6){{margin-top:-4px}}
.texture{{display:block;width:100%;height:100%;background:var(--orange);fill:#fff}} .card-1 .texture,.card-3 .texture{{background:var(--peach)}} .copy{{padding:1rem 1rem 1.4rem;border-top:1.5px solid var(--orange)}}
.question{{color:var(--orange);font-size:.72rem;font-weight:700;margin:0 0 .85rem}} h2{{font-size:1.22rem;line-height:1.08;margin:0 0 .75rem;letter-spacing:-.025em}} .summary{{font-size:.9rem;line-height:1.45;margin:0}} .read-more{{display:flex;justify-content:space-between;gap:1rem;margin-top:1.35rem;padding-top:.65rem;border-top:1px solid #ddd;font:700 .66rem/1 monospace;text-transform:uppercase;letter-spacing:.04em;opacity:.62}}
.card:focus-visible{{outline:3px solid var(--ink);outline-offset:4px;z-index:2}} .card:active{{translate:0 2px}}
@keyframes card-wiggle{{0%{{rotate:0deg;translate:0 0}}28%{{rotate:-1.1deg;translate:0 -5px}}58%{{rotate:.8deg;translate:0 -7px}}82%{{rotate:-.35deg;translate:0 -5px}}100%{{rotate:0deg;translate:0 -4px}}}}
@media (hover:hover) and (pointer:fine){{.card:hover{{animation:card-wiggle .36s cubic-bezier(.2,.8,.3,1) both;box-shadow:8px 10px 0 rgba(40,35,31,.12);z-index:3}}}}
dialog{{width:100vw;max-width:none;height:100dvh;max-height:none;margin:0;padding:0;border:0;background:rgba(40,35,31,.72);color:var(--ink)}} dialog::backdrop{{background:rgba(40,35,31,.72)}} .modal-shell{{min-height:100%;display:grid;place-items:center;padding:clamp(1rem,4vw,4rem)}}
.modal-card{{width:min(1040px,100%);min-height:min(720px,calc(100dvh - 4rem));display:grid;grid-template-columns:minmax(260px,38%) 1fr;background:#fff;border:2px solid var(--orange);box-shadow:18px 22px 0 rgba(0,0,0,.24);position:relative;overflow:hidden}}
.modal-art{{background:var(--orange);min-height:280px;display:grid;place-items:center;overflow:hidden}} .modal-art .texture{{height:100%;width:100%}} .modal-copy{{padding:clamp(2rem,6vw,5rem);display:flex;flex-direction:column;justify-content:center}} .modal-question{{color:var(--orange);font:700 .78rem/1.2 monospace;text-transform:uppercase;letter-spacing:.05em}} .modal-headline{{font-size:clamp(2.5rem,6vw,5.8rem);line-height:.88;letter-spacing:-.06em;margin:.4em 0 .32em}} .modal-summary{{font-size:1.05rem;font-weight:700;line-height:1.45;margin:0 0 1.4rem}} .modal-detail{{font-size:clamp(1rem,1.6vw,1.25rem);line-height:1.65;max-width:58ch;margin:0}}
.modal-close{{position:absolute;right:1rem;top:1rem;width:48px;height:48px;border:1.5px solid var(--ink);background:#fff;font-size:1.7rem;cursor:pointer;z-index:2}} .modal-close:focus-visible,.modal-nav button:focus-visible{{outline:3px solid var(--orange);outline-offset:3px}} .modal-nav{{display:flex;gap:.5rem;margin-top:2.5rem}} .modal-nav button{{border:1.5px solid var(--ink);background:#fff;padding:.8rem 1rem;font-weight:700;cursor:pointer}} body.modal-open{{overflow:hidden}}
.provn-watermark{{position:fixed;left:14px;bottom:14px;z-index:20;display:flex;align-items:center;gap:8px;padding:7px 10px;background:rgba(247,244,238,.92);border:1px solid rgba(40,35,31,.18);color:var(--ink);text-decoration:none;box-shadow:3px 4px 0 rgba(40,35,31,.09);backdrop-filter:blur(6px)}} .provn-watermark span{{font:600 9px/1 monospace;text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}} .provn-watermark img{{display:block;width:92px;height:auto}} .provn-watermark:hover{{border-color:var(--orange)}} .provn-watermark:focus-visible{{outline:3px solid var(--orange);outline-offset:3px}}
footer{{margin-top:3rem;font:11px/1.5 monospace;border-top:1px solid;padding-top:1rem;word-break:break-word}}
@media (max-width: 1050px){{.grid{{grid-template-columns:repeat(3,1fr)}}}}
@media (max-width: 700px){{main{{padding:3rem 1rem}} header{{display:block}} .grid{{grid-template-columns:1fr}} .card{{min-height:330px;transform:none!important;margin:-1px 0 0!important}} .modal-shell{{padding:0}} .modal-card{{min-height:100dvh;grid-template-columns:1fr;grid-template-rows:28vh 1fr;box-shadow:none;border-width:0}} .modal-copy{{padding:2rem 1.4rem 3rem;justify-content:start}} .modal-headline{{font-size:clamp(2.5rem,13vw,4.5rem)}}}}
@media (prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important}}.card{{transform:none!important;transition:none!important;animation:none!important}}}}
@media print{{main{{padding:.2in}} .card{{transform:none!important;break-inside:avoid}} footer,.read-more,dialog,script,.provn-watermark{{display:none!important}}}}
</style></head><body><main><header><h1>glasshouse</h1><p class="period">{escape(str(report.get('period','')))}</p></header>
<section class="grid" aria-label="Your coding-agent activity cards">{"".join(cards)}</section>
<footer aria-label="Collection summary">LOCAL ONLY · {summary}</footer></main>
<a class="provn-watermark" href="https://provn.co" target="_blank" rel="noopener noreferrer" aria-label="Powered by Provn"><span>Powered by</span><img src="{provn_logo}" alt="Provn"></a>
<dialog id="card-dialog" aria-modal="true" aria-labelledby="modal-headline"><div class="modal-shell">
<article class="modal-card"><button class="modal-close" data-action="close" aria-label="Close expanded card">×</button>
<div class="modal-art" aria-hidden="true"></div><div class="modal-copy"><p class="modal-question"></p><h2 class="modal-headline" id="modal-headline"></h2><p class="modal-summary"></p><p class="modal-detail"></p>
<nav class="modal-nav" aria-label="Expanded card navigation"><button data-action="previous">← Previous</button><button data-action="next">Next →</button></nav></div></article></div></dialog>
<script>
(() => {{
  const cards = [...document.querySelectorAll('.card')];
  const dialog = document.querySelector('#card-dialog');
  const closeButton = dialog.querySelector('[data-action="close"]');
  let currentIndex = -1;
  let lastTrigger = null;

  function fill(index, updateHash = true) {{
    const card = cards[index];
    if (!card) return;
    currentIndex = index;
    dialog.querySelector('.modal-question').textContent = card.querySelector('.question').textContent;
    dialog.querySelector('.modal-headline').textContent = card.querySelector('h2').textContent;
    dialog.querySelector('.modal-summary').textContent = card.querySelector('.summary').textContent;
    dialog.querySelector('.modal-detail').textContent = card.querySelector('.detail').textContent;
    dialog.querySelector('.modal-art').replaceChildren(card.querySelector('.texture').cloneNode(true));
    if (updateHash) history.replaceState(null, '', '#card-' + card.dataset.cardId);
  }}

  function openCard(index, trigger = cards[index], updateHash = true) {{
    lastTrigger = trigger;
    fill(index, updateHash);
    cards.forEach(card => card.setAttribute('aria-expanded', 'false'));
    cards[index].setAttribute('aria-expanded', 'true');
    if (!dialog.open) dialog.showModal();
    document.body.classList.add('modal-open');
    closeButton.focus();
  }}

  function closeCard() {{
    if (dialog.open) dialog.close();
    document.body.classList.remove('modal-open');
    history.replaceState(null, '', location.pathname + location.search);
    cards.forEach(card => card.setAttribute('aria-expanded', 'false'));
    if (lastTrigger) lastTrigger.focus();
  }}

  cards.forEach((card, index) => {{
    card.addEventListener('click', () => openCard(index, card));
    card.addEventListener('keydown', event => {{
      if (event.key === 'Enter' || event.key === ' ') {{ event.preventDefault(); openCard(index, card); }}
    }});
  }});
  dialog.addEventListener('click', event => {{ if (event.target === dialog || event.target.classList.contains('modal-shell')) closeCard(); }});
  dialog.addEventListener('cancel', event => {{ event.preventDefault(); closeCard(); }});
  closeButton.addEventListener('click', closeCard);
  dialog.querySelector('[data-action="previous"]').addEventListener('click', () => fill((currentIndex - 1 + cards.length) % cards.length));
  dialog.querySelector('[data-action="next"]').addEventListener('click', () => fill((currentIndex + 1) % cards.length));
  addEventListener('hashchange', () => openFromHash(false));
  function openFromHash(updateHash = false) {{
    const index = cards.findIndex(card => '#card-' + card.dataset.cardId === location.hash);
    if (index >= 0) openCard(index, cards[index], updateHash);
  }}
  openFromHash(false);
}})();
</script></body></html>'''
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
