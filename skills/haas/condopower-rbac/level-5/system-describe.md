# system.describe — Level 5

## Uso
- Exclusivo do superadmin (level 5)
- Catálogo autoritativo de todos os métodos da API

## Fluxo

### Todos os métodos
```json
{"method":"system.describe","params":{}}
```

### Um método específico
```json
{"method":"system.describe","params":{"method_name":"form.pulse"}}
```

## Regras
- Esta skill (`condopower-rbac`) pode envelhecer; o catálogo NÃO
- Se houver divergência entre a skill e `system.describe`, o catálogo está certo
- Use quando houver dúvida sobre contrato de qualquer método