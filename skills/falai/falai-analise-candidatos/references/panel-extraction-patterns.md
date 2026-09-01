# Panel Extraction Patterns — InHire List View

Técnicas confiáveis para extrair dados do painel lateral de candidato após clicar no botão de
nome na visualização em Lista (`/jobs/<uuid>`).

## O problema

Quando você clica num botão de candidato na lista, o InHire (SPA React) abre um painel lateral.
Nesse momento, `document.body.innerText` retorna **TODO o texto da página** — tanto a lista de
candidatos quanto o conteúdo do painel — concatenados em uma única string.

O conteúdo do painel SEMPRE vem DEPOIS do marcador de paginação da lista.

## Técnica primária: split no marcador de paginação

```js
var body = document.body.innerText;
var parts = body.split('1 a 10 de 120 itens');
if (parts.length > 1) {
  var panelContent = parts[1].trim();  // ← dados do painel lateral
}
```

**Funciona porque:**
- O marcador de paginação é renderizado pela lista, NÃO pelo painel
- Todo o conteúdo do painel (header, campos personalizados, pretensão, CV) vem DEPOIS desse marcador
- O split isola perfeitamente os dados do painel

## Fallback: paginação variável

O marcador exato depende do número de itens e página atual:
- `"1 a 10 de 120 itens"` — página 1 de 12 (120 itens)
- `"1 a 2 de 2 itens"` — quando filtrado por busca (2 itens)
- `"1 a 10 de 136 itens"` — página 1 de 14 (136 itens)

Se o marcador exato for desconhecido, use um padrão mais genérico:

```js
var body = document.body.innerText;
// Tenta split pelo início do texto de paginação comum
var parts = body.split('1 a ');
if (parts.length > 1) {
  var idx = body.indexOf(parts[parts.length - 1]);
  if (idx > 100) {
    var panelContent = body.substring(idx);
  }
}
```

## Fallback último: substring do final

Se ambos os splits falharem, pegue os últimos 3000 caracteres do body — o painel geralmente
fica no final:

```js
var body = document.body.innerText;
var panelContent = body.substring(body.length - 3000);
```

## O que o painel contém (ordem típica)

```
<Iniciais>
<Nome Completo>
<Cidade - Estado, País>
<Avaliações (0 0 0)>
Reprovar Segue Adicionar tag
<Vaga Name>
Etapa:<Stage>
Ativo
Outras vagas (N)
Geral | Campos personalizados
Pretensão salarial R$ X.XXX,XX <Modelo>
<Cidade> - <Estado>, Brasil
+55****XXXX
<email>
/<linkedin-slug>
Disposto(a) a trabalhar no modelo presencial...?
Sim / Não
Fonte <LinkedIn/Indeed/Página de Vaga>
...
Currículo (CV completo)
```

## Fluxo completo para extração em lote

1. Navegue para `/jobs/<uuid>` (logado)
2. Clique em "Lista" (modo tabela)
3. Para cada candidato alvo:
   a. Clique no `button` com o nome (NÃO no `link`)
   b. Aguarde 1-2s para o painel renderizar
   c. Extraia com `split('1 a 10 de ...')` 
   d. Salve os dados na conversa (execute_code ou memorização)
   e. Pressione Escape para fechar o painel (opcional)
4. Se a sessão expirar, re-logue e continue de onde parou

## Pitfalls

- **NÃO use `browser_snapshot` para extrair dados do painel** — o snapshot da SPA frequentemente
  trunca ou omite o conteúdo do painel. `browser_console` com `document.body.innerText` é sempre
  mais confiável.
- **O botão de fechar painel pode não existir** — pressione `Escape` para fechar.
- **Após re-login, a view padrão é Kanban** — clique em "Lista" imediatamente.
- **O ID do candidato pode ser extraído do DOM**, mas raramente é necessário — o nome + dados do
  painel são suficientes para a análise.