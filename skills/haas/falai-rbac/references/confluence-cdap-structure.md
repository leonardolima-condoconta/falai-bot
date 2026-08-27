# Confluence CDAP — Estrutura de Procedimentos de People

Espaço: **Central de Ajuda People (CDAP)**
Homepage ID: `677052681`
URL: https://condoconta.atlassian.net/wiki/spaces/CDAP/overview

Mapeado em 25/08/2026. Atualizar se novas páginas forem adicionadas.

## Estrutura completa (árvore)

```
Central de Ajuda People (CDAP)
├─ Artigo de instruções          (placeholder — vazio)
├─ Artigo de solução de problemas (placeholder — vazio)
├─ Plano de Cargos e Salários 2026
│  └─ Status - Plano de Cargos e Salários
│     (38 descrições de cargo individuais, de Analista a Head)
├─ Fluxo do Projeto de Desenvolvimento Pessoal
   ├─ Etapa 1 — Autoavaliação do liderado
   ├─ Etapa 2 — Avaliação do líder sobre o liderado
   ├─ Etapa 3 — 1:1 de calibragem
   ├─ Etapa 4 — Enquadramento no 9 Box
   └─ Etapa 5 — Definição do PDI
```

## 38 cargos documentados (JDs individuais)

Cada cargo tem página própria sob Plano de Cargos e Salários 2026:

| Cargo | Page ID |
|---|---|
| Analista AI Expert | 2580578307 |
| Analista Administrativo | 2580807682 |
| Analista Cobrança | 2580709400 |
| Analista Crédito/Risco | 2579824643 |
| Analista Financeiro | 2579824665 |
| Analista Jurídico | 2580611091 |
| Analista Marketing | 2580414467 |
| Analista Onboarding | 2579726341 |
| Analista Relac. | 2579660805 |
| Analista Service Desk | 2581069825 |
| Analista Suporte | 2580545560 |
| Analista Tesouraria | 2580709377 |
| Analista de Endomarketing | 2580414488 |
| Analista de MIS | 2580774934 |
| Assist. Cobrança | 2580676612 |
| Assist. Implantação | 2580938753 |
| Assist. Jurídico | 2579922948 |
| Backend Lead | 2579890204 |
| Business Partner (HRBP) | 2580152326 |
| Cientista de Dados | 2580611113 |
| Coord. Cobrança | 2580905986 |
| Coord. Controladoria | 2580774913 |
| Coord. Onboarding | 2579824686 |
| Coord. Relac. | 2580971521 |
| Coord. Suporte | 2581004290 |
| Dev Backend | 2580348933 |
| Dev Front-End | 2579791876 |
| Dev Mobile | 2580185091 |
| Eng. de Dados | 2580250628 |
| GPM (Group Product Manager) | 2579857413 |
| Gerente Cobrança | 2580545539 |
| Gerente Growth | 2579890179 |
| Gerente Tesouraria | 2580742147 |
| Head AI Expert | 2580774955 |
| Product Designer | 2580840451 |

## O que NÃO está documentado no Confluence

Os seguintes procedimentos de People **não têm página** no CDAP (nem em PT ou CCD):

- Política de onboarding de novos colaboradores
- Política de offboarding / desligamento
- Código de conduta / dress code
- Política de trabalho remoto / presencial
- Administração de benefícios (VT, VR, plano de saúde, gympass)
- Gestão de férias e ausências
- Comunicação interna / newsletters / campanhas
- Eventos corporativos / endomarketing

Esses procedimentos existem operacionalmente mas não estão formalizados na wiki.

## Como consultar

Para buscar no CDAP via API Confluence:
```
GET /wiki/rest/api/search?cql=text ~ "termo" AND space = "CDAP" AND type = page
GET /wiki/rest/api/content/{id}/child/page?limit=50
```

Autenticação: Basic auth com `JIRA_EMAIL:JIRA_API_TOKEN` (mesmas creds do Jira).
Homepage tem filhos de nível 1; cada filho pode ter seus próprios filhos (nível 2).

## Pitfalls

- As duas páginas placeholder ("Artigo de instruções", "Artigo de solução de problemas") são
  templates vazios — provavelmente vieram com o space template do Confluence.
- O espaço PT (`people-data-sources.md`) tem JDs e templates complementares.
- Faixas salariais NÃO estão no Confluence — só no Google Drive
  (`1ZCylbQekuaaf19VsmvCcDo-TZPqM_wRB`).