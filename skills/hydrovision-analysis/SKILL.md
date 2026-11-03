---
name: hydrovision-analysis
description: Consultar dados do HydroVision via MCP, resolver entidades e comparar indicadores de vazamentos, setores, usuários e investigações com escopo e conceitos explícitos.
---

# Análises do HydroVision

Responda à pergunta com as tools da conexão HydroVision disponível. Elas são somente
leitura. O prefixo varia entre clientes; schemas atuais e metadados das respostas
prevalecem sobre os exemplos desta skill.

## Consultar

1. Use `get_context` ao iniciar ou mudar o escopo. Sem empresa informada, use a
   selecionada e declare a escolha; não amplie para todas as empresas autorizadas.
2. Resolva nomes, endereços, MACs e códigos com `resolve_entities`. Desambigue quando
   houver candidatos incompatíveis. Não confunda conta, funcionário, equipamento e ponto.
3. Consulte `describe_data` antes de construir consultas de contrato desconhecido.
   Prefira `query_data` para registros e agregações; aprofunde com tools de detalhe.
4. Defina período, fuso e evento. Preserve `scope`, `period`, `method`, `coverage`,
   `warnings` e paginação. Agregue a população completa antes de apresentar totais.
5. Relacione achados a objetos identificados e distinga observação, estimativa e hipótese.

Leia [domain.md](references/domain.md) para conceitos e diferenças de métricas;
[concepts.json](references/concepts.json) para objetos, campos e relações;
[tools.json](references/tools.json) para selecionar uma tool;
[workflows.md](references/workflows.md) para paginação, cruzamentos, comparação e CSVs.
Carregue apenas as referências necessárias à pergunta.

## Apresentar

Use nomes canônicos em português; mantenha códigos técnicos nos argumentos das tools.
Informe recorte, unidades e limitações que mudem a conclusão. Não transforme nulo em zero,
uma página em total, eventos em casos ou economia projetada em volume medido.

Imagens principais aparecem junto ao texto, com legenda e objeto de origem. As demais
ficam em apêndice visual incorporado ao documento; no chat, em galeria na própria
resposta. Não substitua imagens por links, redirecionamentos, nomes ou base64.
Leia [images.md](references/images.md) ao consultar fotos ou produzir conteúdo visual.
Se o cliente não permitir apresentar os bytes, declare a evidência indisponível;
não afirme que a imagem foi exibida ou anexada.

Arquivos são gerados quando solicitados, usando as capacidades disponíveis do cliente.
Leia [client.md](references/client.md) para autenticação, arquivos e imagens no ambiente
atual. Confirme que o arquivo existe e que o conteúdo foi verificado antes da entrega.
