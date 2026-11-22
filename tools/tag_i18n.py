"""Tag translatable elements in index.html with data-i18n keys (in place)
and write i18n/en.json with the English source HTML for each key.
Run again after editing texts: existing keys are kept, new elements get new keys."""
import json, re, os, sys
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'index.html')
src = open(P, encoding='utf-8').read()
soup = BeautifulSoup(src, 'html.parser')

INLINE = {'b', 'strong', 'a', 'br', 'em', 'svg', 'use', 'span'}
CAND = {'p', 'h1', 'h2', 'h3', 'span', 'b', 'a', 'summary', 'label', 'button', 'small', 'li', 'figcaption', 'div', 'option', 'blockquote', 'footer'}
SKIP_CLASSES = {'latin', 'brand', 'mlabels', 'dot', 'pin', 'months'}
SKIP_IDS = {'calTitle', 'calStatus', 'quote', 'guests', 'priceList', 'mbFrom', 'wxText', 'formErr', 'doneTitle', 'doneText', 'doneBody', 'footMail', 'lbCount', 'places'}

def has_letters(t): return re.search(r'[A-Za-zÅÄÖåäö]{2,}', t) is not None

def qualifies(el):
    if el.name not in CAND: return False
    if el.get('id') in SKIP_IDS: return False
    if SKIP_CLASSES & set(el.get('class') or []): return False
    if el.find_parent(['svg', 'script', 'style', 'select', 'blockquote']) and el.name != 'blockquote': return False
    for d in el.descendants:
        if isinstance(d, Tag):
            if d.name not in INLINE and d.find_parent('svg') is None: return False
            if d.get('id') in SKIP_IDS and d.get('id') != 'rampDist': return False
            if d.name == 'span' and (set(d.get('class') or []) - {'m-hide'}): return False
    text = ''.join(t for t in el.find_all(string=True) if t.find_parent('svg') is None)
    return has_letters(text)

body = soup.body
chosen = []
def walk(node):
    for ch in node.children:
        if not isinstance(ch, Tag) or ch.name in ('script', 'style', 'svg', 'select', 'dialog'): continue
        if ch.name == 'blockquote': continue          # guest reviews stay in the original language
        if ch.get('data-i18n'): chosen.append(ch); continue
        if qualifies(ch): chosen.append(ch); continue
        walk(ch)
walk(body)

en_path = os.path.join(ROOT, 'i18n', 'en.json')
en = json.load(open(en_path)) if os.path.exists(en_path) else {}
used = set(en)
def slug(el):
    t = ' '.join(''.join(x for x in el.find_all(string=True) if x.find_parent('svg') is None).split())
    base = re.sub(r'[^a-z0-9]+', '-', t.lower())[:40].strip('-') or 'k'
    k, i = base, 2
    while k in used: k = f'{base}-{i}'; i += 1
    used.add(k); return k

# insert attributes by source position (no re-serialisation of the file)
lines = src.split('\n'); offs = [0]
for ln in lines: offs.append(offs[-1] + len(ln) + 1)
inserts = []
for el in chosen:
    inner = ''.join(str(c) for c in el.contents if not (isinstance(c, Tag) and c.name == 'svg')).strip()
    if el.get('data-i18n'):
        en[el['data-i18n']] = inner; continue
    k = slug(el); en[k] = inner
    pos = offs[el.sourceline - 1] + el.sourcepos + 1 + len(el.name)
    assert src[pos - len(el.name) - 1:pos] == '<' + el.name, (k, src[pos-20:pos+5])
    inserts.append((pos, f' data-i18n="{k}"'))
for pos, txt in sorted(inserts, reverse=True):
    src = src[:pos] + txt + src[pos:]
open(P, 'w', encoding='utf-8').write(src)
json.dump(en, open(en_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(chosen), 'elements,', len(inserts), 'newly tagged')
