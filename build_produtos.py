# -*- coding: utf-8 -*-
"""Gera produtos.json a partir do CSV exportado do Wix (catalog_products.csv).

Uso:  python build_produtos.py "caminho/do/catalog_products.csv"

Cada categoria do quiz (ids de DEST em index.html) recebe os produtos do site que
se encaixam nela, ordenados por relevância, com nome, preço, foto (CDN do Wix) e
palavras-chave pra combinar com o perfil da pessoa no resultado. O quiz não depende
deste arquivo pra funcionar: sem ele, o resultado mostra só as categorias.
"""
import csv, io, json, re, sys, unicodedata, collections

src = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\André Pereira\Downloads\catalog_products (5).csv"
rows = list(csv.DictReader(io.StringIO(open(src, 'rb').read().decode('utf-8-sig'))))

def norm(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()

def thumb(media):
    return f"https://static.wixstatic.com/media/{media}/v1/fit/w_480,h_480,q_85/f.jpg"

SITE = 'https://www.itscoolprazerebemestar.com.br/'

def wix_slug(name):
    """Regra do Wix pra URL de produto: minúsculo, acentos mantidos, pontuação some
    (7,5g vira 75g; D'Água vira dágua), qualquer outro separador vira hífen."""
    t = name.lower().strip()
    t = re.sub(r"['’`´\",.()]", '', t)
    t = re.sub(r'[^0-9a-zà-ÿ]+', '-', t)
    return t.strip('-')

# URLs reais: abre cada página do sitemap e guarda título -> URL. O slug do Wix não dá pra
# deduzir do nome (é cortado em 80 caracteres e fica fixo quando o produto é renomeado).
import urllib.request, urllib.parse, html, time
from concurrent.futures import ThreadPoolExecutor
def baixar(u, tent=3):
    for i in range(tent):
        try:
            q = urllib.parse.quote(u, safe=':/%')
            return urllib.request.urlopen(urllib.request.Request(q, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'ignore')
        except Exception:
            time.sleep(2 * (i + 1))
    return ''
xml = baixar(SITE + 'store-products-sitemap.xml')
LOCS = [urllib.parse.unquote(u) for u in re.findall(r'<loc>([^<]+)</loc>', xml)]
def titulo(u):
    m = re.search(r'<title[^>]*>(.*?)</title>', baixar(u), re.S)
    return u, re.sub(r'\s*\|\s*My Site\s*$', '', html.unescape(m.group(1))).strip() if m else ''
with ThreadPoolExecutor(6) as ex:
    PAGINAS = list(ex.map(titulo, LOCS))
# o Wix limita rajadas: repete devagar as que não responderam
for rodada in range(3):
    falta = [u for u, t in PAGINAS if not t]
    if not falta: break
    time.sleep(20)
    with ThreadPoolExecutor(2) as ex:
        novas = dict(ex.map(titulo, falta))
    PAGINAS = [(u, t or novas.get(u, '')) for u, t in PAGINAS]
POR_TITULO = {norm(t): u for u, t in PAGINAS if t}
print('sitemap:', len(LOCS), 'páginas;', len(POR_TITULO), 'títulos lidos')

medias = collections.defaultdict(list)
for r in rows:
    if r['fieldType'] == 'MEDIA' and r['media']:
        medias[r['handle']].append(r['media'])

prods = []
for r in rows:
    if r['fieldType'] != 'PRODUCT' or r['visible'] != 'true':
        continue
    m = medias.get(r['handle'], [])
    prods.append({
        'nome': r['name'].strip(),
        'preco': r['price'],
        'img': thumb(m[0]) if m else '',
        'cats': [norm(c).replace(' ', '-') for c in (r['categorySlugs'] or '').split(';') if c.strip()],
        'nm': norm(r['name']),
        'kw': norm(r['name'] + ' ' + (r['plainDescription'] or '')[:400]),
        'slug': wix_slug(r['name']),
    })
    prods[-1]['url'] = POR_TITULO.get(prods[-1]['nm'], '')

def has(p, *cs): return any(c in p['cats'] for c in cs)
def nome(p, *ws): return any(w in p['nm'] for w in ws)
def desc(p, *ws): return any(w in p['kw'] for w in ws)

VIB = ('nao-penetraveis', 'penetraveis', 'sugadores', 'dupla-estimulacao', 'de-casal', 'controle-remoto-e-app', 'vibradores-1')
# (filtro, pontuação por palavra no nome, exclusões no nome)
REGRAS = {
    'vib-externo':   (lambda p: has(p, 'nao-penetraveis', 'sugadores'), ['sugador', 'succao', 'pulsa', 'ondas de pressao', 'clitori', 'bullet', 'capsula'], []),
    'vib-interno':   (lambda p: has(p, 'penetraveis'), ['ponto g', 'curvado', 'golfinho', 'penetra'], []),
    'vib-dois':      (lambda p: has(p, 'de-casal', 'controle-remoto-e-app'), ['casal', 'controle', 'app', 'wireless', 'calcinha', 'vestivel'], []),
    'vib-comecar':   (lambda p: has(p, *VIB) and nome(p, 'bullet', 'capsula', 'batom', 'golfinho', 'mini varinha'), ['bullet', 'batom', 'power', 'capsula'], []),
    'vib-sensacoes': (lambda p: has(p, 'dupla-estimulacao'), ['sugador', 'succao', 'pulsa', 'ondas', 'dupla', 'rabbit'], []),
    'vib-peniano':   (lambda p: has(p, 'aneis-penianos'), ['anel', 'vibra'], []),
    'geis':          (lambda p: has(p, 'lubrificantes', 'geis-de-sensacoes'), ['lubrificante', 'deslizante', 'gel'], []),
    'gel-neutro':    (lambda p: has(p, 'lubrificantes'), ['neutro', 'natural', 'base de agua', 'hialur', 'aloe', 'comfort', 'intimo'], ['hot', 'ice', 'quente', 'gelad', 'excit', 'eletriz', 'vibra', 'siliconado', 'silicone', 'beij', 'comest', 'sabor', 'chiclete', 'morango']),
    'gel-termico':   (lambda p: has(p, 'geis-de-sensacoes', 'lubrificantes') and nome(p, 'hot', 'ice', 'quente', 'gelad', 'esquenta', 'refresc', 'termic', 'fire', 'frio'), ['hot', 'ice', 'quente', 'gelad', 'esquenta', 'refresc'], ['retard', 'prolong', 'dessensib']),
    'gel-agua':      (lambda p: has(p, 'lubrificantes', 'geis-e-lubrificantes') and nome(p, 'siliconado', 'silicone', 'silicon', 'aquatic'), ['siliconado', 'silicone'], []),
    'gel-resistente':(lambda p: has(p, 'lubrificantes', 'geis-e-lubrificantes') and nome(p, 'siliconado', 'silicone', 'silicon', 'longa duracao', 'duradour'), ['siliconado', 'silicone', 'longa'], []),
    'gel-retardar':  (lambda p: has(p, 'adstringentes-e-retardantes') and nome(p, 'retard', 'prolong', 'dessensib', 'long'), ['retard', 'prolong', 'dessensib'], ['anal', 'garganta']),
    'gel-estimulos': (lambda p: has(p, 'geis-de-sensacoes'), ['excit', 'eletriz', 'vibrador liquido', 'climax', 'multiplas', 'pulsa'], []),
    'jogos':         (lambda p: has(p, 'jogos-e-brincadeiras'), ['casal', 'dados', 'tabuleiro', 'roleta'], []),
    'massagem':      (lambda p: has(p, 'massagem-e-experiencias', 'velas', 'massagens', 'sais-de-banho'), ['vela', 'oleo', 'massagem', 'sais', 'banho'], []),
    'aces-explorar': (lambda p: has(p, 'para-explorar-masturbar-e-estimular'), ['masturbador', 'penis', 'realistico', 'dildo', 'egg'], []),
    'aces-dominar':  (lambda p: has(p, 'para-dominar-fantasiar-e-brincar'), ['venda', 'algema', 'chicote'], []),
    'higiene':       (lambda p: has(p, 'higiene-intima') and not nome(p, 'anal', 'masculino'), ['sabonete intimo', 'feminino', 'higieniz', 'brinquedo', 'toy'], []),
    'cosmeticos':    (lambda p: has(p, 'cosmeticos-intimos') and not nome(p, 'anal', 'gel ', 'lubrificante'), ['perfume', 'oleo', 'serum', 'creme', 'desodorante', 'mousse', 'elixir'], []),
    'hidratacao':    (lambda p: nome(p, 'hidrat', 'hialur') and nome(p, 'vaginal', 'intim', 'hialur', 'aloe') and not nome(p, 'anal', 'cabel', 'virilha'), ['hidratante', 'vaginal', 'hialur', 'aloe'], []),
    'pelvica':       (lambda p: has(p, 'saude-pelvica'), ['pompoar', 'cones', 'dilatador', 'bolas', 'condutor'], []),
    'anal-plugs':    (lambda p: has(p, 'plug'), ['plug', 'pequeno', 'iniciante', 'kit'], []),
    'anal-vib':      (lambda p: has(p, 'plug') and nome(p, 'vibra', 'vibro', 'controle'), ['vibra', 'vibro', 'controle'], []),
    'anal-gel':      (lambda p: has(p, 'anal-geis-e-lubrificantes') and not nome(p, 'kit'), ['facilitador', 'dessensib', 'hialur', 'anal', 'lubrificante'], ['beijo', 'comest', 'yummy', 'porta dos fundos']),
    'anal-higiene':  (lambda p: has(p, 'anal-higiene-e-cuidados'), ['ducha', 'higieniz', 'hidratante'], []),
    'kits':          (lambda p: has(p, 'kits'), ['kit'], []),
    'sale':          (lambda p: has(p, 'sale'), [], []),
}

out = {}
for cid, (filtro, pontos, excl) in REGRAS.items():
    lst = []
    for p in prods:
        if not filtro(p) or not p['url']: continue
        if any(e in p['nm'] for e in excl): continue
        score = sum(2 for w in pontos if w in p['nm']) + sum(1 for w in pontos if w in p['kw']) + (3 if p['img'] else 0)
        lst.append((score, p))
    lst.sort(key=lambda x: (-x[0], x[1]['nome']))
    out[cid] = [{'n': p['nome'], 'p': p['preco'], 'i': p['img'], 'u': p['url'], 'k': p['kw'][:160]} for _, p in lst[:24]]
    print(f"{cid:15} {len(lst):3}  " + ' | '.join(p['nome'][:38] for _, p in lst[:3]))

json.dump(out, open('produtos.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('sem página (fora do resultado):', [p['nome'] for p in prods if not p['url']])
print('produtos.json gerado com', sum(len(v) for v in out.values()), 'entradas;', sum(1 for v in out.values() for p in v if p['u']), 'com URL própria;', sum(1 for p in prods if not p['url']), 'produtos do CSV sem página no sitemap')
