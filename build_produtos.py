# -*- coding: utf-8 -*-
"""Gera produtos.json a partir do CSV exportado do Wix (catalog_products.csv).

Uso:  python build_produtos.py "caminho/do/catalog_products.csv"

Cada categoria do quiz (ids de DEST em index.html) recebe os produtos do site que
se encaixam nela, ordenados por relevância, com nome, preço, foto (CDN do Wix) e
palavras-chave pra combinar com o perfil da pessoa no resultado. O quiz não depende
deste arquivo pra funcionar: sem ele, o resultado mostra só as categorias.
"""
import csv, io, json, re, sys, unicodedata, collections

src = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\André Pereira\Downloads\catalog_products (1).csv"
rows = list(csv.DictReader(io.StringIO(open(src, 'rb').read().decode('utf-8-sig'))))

def norm(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()

def thumb(media):
    return f"https://static.wixstatic.com/media/{media}/v1/fill/w_480,h_480,al_c,q_85/f.jpg"

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
        'slug': re.sub(r'\s+', '-', norm(r['name'])),
    })

def has(p, *cs): return any(c in p['cats'] for c in cs)
def nome(p, *ws): return any(w in p['nm'] for w in ws)
def desc(p, *ws): return any(w in p['kw'] for w in ws)

GEL = lambda p: has(p, 'geis-e-lubrificantes') and not has(p, 'anal')
# coisas que não são "lubrificante pra relação" mesmo estando em géis
NAO_LUB = ('calda', 'garganta', 'adstringente', 'clareador', 'dilatador', 'vasodilat', 'excitante masculino', 'potencializador', 'man force', 'sempre virgem', 'spray', 'beijo grego', 'grego')

# (filtro, pontuação por palavra no nome, exclusões no nome)
REGRAS = {
    'vib-externo':   (lambda p: has(p, 'para-estimulo-externo'), ['sugador', 'succao', 'pulsa', 'ondas de pressao', 'clitori', 'bullet', 'capsula'], []),
    'vib-interno':   (lambda p: has(p, 'para-estimulo-interno'), ['ponto g', 'curvado', 'golfinho', 'penetra'], []),
    'vib-dois':      (lambda p: has(p, 'para-usar-a-dois'), ['casal', 'controle', 'app', 'wireless', 'calcinha', 'vestivel'], []),
    'vib-comecar':   (lambda p: has(p, 'para-comecar-a-explorar'), ['bullet', 'batom', 'power', 'golfinho'], []),
    'vib-sensacoes': (lambda p: has(p, 'para-diferentes-sensacoes'), ['sugador', 'succao', 'pulsa', 'ondas', 'ponto g e sugador', 'dupla'], []),
    'vib-peniano':   (lambda p: has(p, 'vibradores', 'acessorios-de-prazer') and nome(p, 'anel', 'peniano'), ['anel', 'vibra'], ['masturbador', 'dilatador']),
    'geis':          (GEL, ['lubrificante', 'deslizante', 'gel'], list(NAO_LUB)),
    'gel-neutro':    (lambda p: GEL(p) and nome(p, 'lubrificante', 'deslizante', 'lub '), ['neutro', 'natural', 'base de agua', 'hialur', 'aloe', 'comfort', 'intimo'], list(NAO_LUB) + ['hot', 'ice', 'quente', 'gelad', 'excit', 'eletriz', 'vibra', 'retard', 'prolong', 'dessensib', 'siliconado', 'silicone', 'beij', 'comest', 'sabor', 'chiclete', 'morango']),
    'gel-termico':   (lambda p: GEL(p) and nome(p, 'hot', 'ice', 'quente', 'gelad', 'esquenta', 'refresc', 'termic', 'fire', 'frio'), ['hot', 'ice', 'quente', 'gelad', 'esquenta', 'refresc'], list(NAO_LUB) + ['retard', 'prolong', 'dessensib']),
    'gel-agua':      (lambda p: GEL(p) and nome(p, 'siliconado', 'silicone', 'silicon', 'banho', 'aquatic'), ['siliconado', 'silicone', 'banho'], list(NAO_LUB)),
    'gel-resistente':(lambda p: GEL(p) and nome(p, 'siliconado', 'silicone', 'silicon', 'longa duracao', 'duradour'), ['siliconado', 'silicone', 'longa'], list(NAO_LUB)),
    'gel-retardar':  (lambda p: GEL(p) and nome(p, 'retard', 'prolong', 'dessensib', 'long'), ['retard', 'prolong', 'dessensib'], ['anal', 'grego']),
    'gel-estimulos': (lambda p: GEL(p) and nome(p, 'excit', 'eletriz', 'vibrador liquido', 'vibra', 'pulsa', 'formig', 'multiplas sensacoes', 'climax', 'estimul', 'tremilik'), ['excit', 'eletriz', 'vibrador liquido', 'climax', 'multiplas'], ['masculino', 'peniano', 'dilatador', 'vasodilat', 'adstringente', 'anal', 'grego', 'spray']),
    'jogos':         (lambda p: has(p, 'jogos-e-brincadeiras'), ['casal', 'dados', 'tabuleiro', 'roleta'], []),
    'massagem':      (lambda p: has(p, 'massagem-e-experiencias', 'velas', 'massagens', 'sais-de-banho'), ['vela', 'oleo', 'massagem', 'sais', 'banho'], []),
    'aces-explorar': (lambda p: has(p, 'para-explorar-masturbar-e-estimular'), ['masturbador', 'penis', 'realistico', 'dildo', 'egg'], []),
    'aces-dominar':  (lambda p: has(p, 'para-dominar-fantasiar-e-brincar'), ['venda', 'algema', 'chicote'], []),
    'higiene':       (lambda p: has(p, 'higiene-intima') and not nome(p, 'anal', 'masculino'), ['sabonete intimo', 'feminino', 'higieniz', 'brinquedo', 'toy'], []),
    'cosmeticos':    (lambda p: has(p, 'cosmeticos-intimos') and not nome(p, 'anal', 'gel ', 'lubrificante'), ['perfume', 'oleo', 'serum', 'creme', 'desodorante', 'mousse', 'elixir'], []),
    'hidratacao':    (lambda p: nome(p, 'hidrat', 'hialur') and nome(p, 'vaginal', 'intim', 'hialur', 'aloe') and not nome(p, 'anal', 'cabel', 'virilha'), ['hidratante', 'vaginal', 'hialur', 'aloe'], []),
    'pelvica':       (lambda p: has(p, 'saude-pelvica'), ['pompoar', 'cones', 'dilatador', 'bolas', 'condutor'], []),
    'anal-plugs':    (lambda p: has(p, 'anal') and nome(p, 'plug'), ['plug', 'pequeno', 'iniciante', 'kit'], []),
    'anal-vib':      (lambda p: has(p, 'anal') and (has(p, 'vibradores-e-estimuladores') or nome(p, 'vibra', 'estimulador', 'tailand')) and not nome(p, 'gel', 'beijo'), ['vibra', 'tailand', 'bolas'], []),
    'anal-gel':      (lambda p: has(p, 'geis-e-lubrificantes-1') and not nome(p, 'kit'), ['facilitador', 'dessensib', 'hialur', 'anal', 'lubrificante'], ['beijo', 'comest', 'yummy', 'porta dos fundos']),
    'anal-higiene':  (lambda p: has(p, 'higiene-e-cuidados') or (has(p, 'anal') and nome(p, 'ducha', 'higien', 'hidratante anal')), ['ducha', 'higieniz', 'hidratante'], []),
    'kits':          (lambda p: has(p, 'kits') or nome(p, 'kit '), ['kit'], []),
    'sale':          (lambda p: False, [], []),
}

out = {}
for cid, (filtro, pontos, excl) in REGRAS.items():
    lst = []
    for p in prods:
        if not filtro(p): continue
        if any(e in p['nm'] for e in excl): continue
        score = sum(2 for w in pontos if w in p['nm']) + sum(1 for w in pontos if w in p['kw']) + (3 if p['img'] else 0)
        lst.append((score, p))
    lst.sort(key=lambda x: (-x[0], x[1]['nome']))
    out[cid] = [{'n': p['nome'], 'p': p['preco'], 'i': p['img'], 's': p['slug'], 'k': p['kw'][:160]} for _, p in lst[:24]]
    print(f"{cid:15} {len(lst):3}  " + ' | '.join(p['nome'][:38] for _, p in lst[:3]))

json.dump(out, open('produtos.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('produtos.json gerado com', sum(len(v) for v in out.values()), 'entradas')
