# it's COOL · Quiz

Quiz de compra guiada da it's COOL. Página estática única (`index.html`), sem build.

- Fotos e logos: `hero.jpg`, `logo-azul.png`
- Links do site: constante `URL_SITE` no início do script em `index.html`
- Grupos de produto e lógica de direcionamento: arrays `GRUPOS`, `KITS` e função `montar()`

Rodar local: qualquer servidor estático na raiz (ex.: `python -m http.server 8765`).

## Fotos de produto no resultado

As fotos ficam em `fotos/` e o mapa `FOTOS` (no início do script em `index.html`) liga cada categoria às suas fotos. A primeira é a capa do card, as seguintes viram miniaturas. Categoria sem foto usa a ilustração. Quando o catálogo estiver no Wix, dá pra trocar os caminhos pelas URLs das imagens dos produtos.
