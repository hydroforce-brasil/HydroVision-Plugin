---
name: hydrovision-visualizations
description: Apresentar dados HydroVision em gráficos, mapas, tabelas e diagramas, com nomes canônicos, unidades, escopo e imagens integradas ao texto.
---

# Visualizações do HydroVision

Adapte a representação à pergunta. O catálogo mapeia as visões do frontend sem exigir
reprodução literal das telas. Use [views.json](references/views.json) para encontrar
blocos, fontes, rotas de referência e limitações. Rotas são identificadores de telas,
não URLs de acesso nem garantias de disponibilidade pelo MCP.

Consulte [domain.md](references/domain.md) e [concepts.json](references/concepts.json)
para nomes e métricas; [tools.json](references/tools.json) para recuperar os dados;
[visualizations.md](references/visualizations.md) para escolher e preparar a representação.

Confirme contexto com `get_context` e contratos com `describe_data`. Identifique período,
empresa, unidade, cobertura e fonte. Não represente páginas incompletas como populações
inteiras; não preencha lacunas como zero nem misture recortes entre blocos.

Renderize gráficos e mapas como figuras incorporáveis, acompanhadas de interpretação
no chat e nos documentos. Use coordenadas/geometrias realmente retornadas; não desenhe
limites de setor ou tubulação a partir de nomes e proximidade. `sector_summary` remove
`boundary`, `pipes` e `installed_loggers`; a linha do tempo não entrega a nuvem completa
de pontos. Declare essas limitações na legenda quando afetarem a leitura.

Leia [images.md](references/images.md). Imagens principais devem aparecer junto ao
texto; as demais, em apêndice visual incorporado ou galeria no chat. Não as substitua
por link, redirecionamento ou nome. Se a renderização falhar, informe o impedimento.
Use [client.md](references/client.md) para os recursos de apresentação do cliente atual.
