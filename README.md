# it's COOL · Quiz

Quiz de compra guiada da it's COOL. Página estática única (`index.html`), sem build.

- Fotos e logos: `hero.jpg`, `logo-azul.png`
- Links do site: constante `URL_SITE` no início do script em `index.html`
- Grupos de produto e lógica de direcionamento: arrays `GRUPOS`, `KITS` e função `montar()`

Rodar local: qualquer servidor estático na raiz (ex.: `python -m http.server 8765`).

## Fotos de produto no resultado

As fotos ficam em `fotos/` e o mapa `FOTOS` (no início do script em `index.html`) liga cada categoria às suas fotos. A primeira é a capa do card, as seguintes viram miniaturas. Categoria sem foto usa a ilustração. Quando o catálogo estiver no Wix, dá pra trocar os caminhos pelas URLs das imagens dos produtos.

## Produtos reais no resultado (produtos.json)

`produtos.json` liga cada categoria do quiz aos produtos cadastrados no Wix. Ele é gerado a partir do CSV exportado do catálogo:

```
python build_produtos.py "caminho/do/catalog_products.csv"
```

As regras de classificação (quais produtos entram em cada categoria do quiz) ficam em `build_produtos.py`, no dicionário `REGRAS`. As fotos vêm direto da CDN do Wix (`static.wixstatic.com/media/<id>`), então não é preciso copiar imagem nenhuma. Cada card do resultado mostra até três produtos da categoria, escolhidos pelas palavras-chave que combinam com o perfil da pessoa, e usa a foto do primeiro como capa. Sem `produtos.json`, o quiz continua funcionando só com as categorias.

Sempre que o catálogo mudar no Wix: exportar o CSV de novo, rodar o script e publicar.
