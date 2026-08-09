# -*- coding: utf-8 -*-
"""リポジトリ直下の教材HTMLを走査して index.html を自動生成する。

各教材HTMLの書き方ルール:
  - <title>教材名 — 説明文</title>  … 「—」の前がカード見出し、後ろが説明文の予備
  - <meta name="description" content="..."> … あればこちらをカードの説明文に使う
  - <meta name="course-order" content="1"> … あれば並び順を指定(なければファイル名順で後ろ)
"""
import re
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"index.html"}


def find_meta(content: str, name: str):
    m = re.search(r'<meta\s+name="' + re.escape(name) + r'"\s+content="([^"]*)"', content)
    return m.group(1).strip() if m else None


def find_title(content: str):
    m = re.search(r"<title>(.*?)</title>", content, re.S)
    return m.group(1).strip() if m else None


courses = []
for p in sorted(ROOT.glob("*.html")):
    if p.name in EXCLUDE:
        continue
    c = p.read_text(encoding="utf-8")
    t = find_title(c) or p.stem
    before, _, after = t.partition("\u2014")  # 「—」で分割
    name = before.strip()
    desc = find_meta(c, "description") or after.strip() or "インタラクティブ教材"
    order = find_meta(c, "course-order")
    order_key = int(order) if order and order.isdigit() else 999
    courses.append((order_key, p.name, name, desc))

courses.sort(key=lambda x: (x[0], x[1]))

cards = []
for i, (_, fname, name, desc) in enumerate(courses, 1):
    badge = "b1" if i % 2 == 1 else "b2"
    cards.append(
        f'''  <a class="course" href="./{fname}">
    <span class="badge {badge}">単元 {i}</span>
    <h2>{html.escape(name)}</h2>
    <p>{html.escape(desc)}</p>
    <span class="go">はじめる →</span>
  </a>'''
    )

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>算数マスター — 中学受験・特殊算のインタラクティブ教材</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#FAFBF7; --grid:#E7ECE4; --ink:#243247; --ink-soft:#5C6B82;
  --kid:#1D9E75; --kid-bg:#DFF4EB; --kid-dark:#0A5540;
  --mom:#D85A30; --mom-bg:#FBE8DF; --mom-dark:#8A3315;
  --marker:#FFE9A8; --radius:12px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  font-family:"Zen Maru Gothic",system-ui,sans-serif;
  color:var(--ink); background:var(--paper);
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:24px 24px;
  min-height:100vh; line-height:1.8;
}
.wrap{max-width:720px;margin:0 auto;padding:48px 20px 80px}
h1{font-size:28px;font-weight:700;margin:0 0 6px;letter-spacing:.02em}
.lead{margin:0 0 32px;color:var(--ink-soft);font-size:14.5px}
a.course{
  display:block;text-decoration:none;color:var(--ink);
  background:#fff;border:2px solid var(--ink);border-radius:var(--radius);
  padding:22px 24px;margin:0 0 20px;
  box-shadow:6px 6px 0 rgba(36,50,71,.12);
  transition:transform .1s ease, box-shadow .1s ease;
}
a.course:hover{transform:translate(-2px,-2px);box-shadow:8px 8px 0 rgba(36,50,71,.16)}
a.course:focus-visible{outline:3px solid var(--kid);outline-offset:3px}
.badge{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:3px 12px;margin:0 0 10px;letter-spacing:.05em}
.b1{background:var(--kid-bg);color:var(--kid-dark);border:1.5px solid var(--kid)}
.b2{background:var(--mom-bg);color:var(--mom-dark);border:1.5px solid var(--mom)}
a.course h2{font-size:20px;font-weight:700;margin:0 0 6px}
a.course p{margin:0;font-size:14px;color:var(--ink-soft)}
.go{display:inline-block;margin-top:12px;font-size:14px;font-weight:700;color:var(--kid-dark)}
footer{margin-top:40px;font-size:12.5px;color:var(--ink-soft)}
@media (prefers-reduced-motion: reduce){ a.course{transition:none} }
</style>
</head>
<body>
<div class="wrap">
  <h1>算数マスター</h1>
  <p class="lead">中学受験の特殊算を、表 → 線分図の小さなステップで身につけるインタラクティブ教材です。好きな単元からはじめよう。</p>

__CARDS__

  <footer>各教材は途中のステップへジャンプして復習できます。</footer>
</div>
</body>
</html>
"""

out = TEMPLATE.replace("__CARDS__", "\n\n".join(cards))
(ROOT / "index.html").write_text(out, encoding="utf-8")
print(f"index.html を生成しました({len(courses)} 教材)")
for _, fname, name, _ in courses:
    print(f"  - {name} ({fname})")
