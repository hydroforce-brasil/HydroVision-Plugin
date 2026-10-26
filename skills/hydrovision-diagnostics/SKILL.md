---
name: hydrovision-diagnostics
description: Diagnosticar frota e loggers HydroVision com saúde funcional, bateria, desempenho e qualidade da telemetria, distinguindo falha operacional de ausência ou atraso dos dados.
---

# Diagnóstico de loggers

Use a conexão MCP HydroVision autenticada, somente leitura. Confirme empresa com
`get_context`, resolva o logger por nome/MAC/ID e consulte o schema atual antes da chamada.
Nunca escolha silenciosamente entre candidatos ambíguos.

Para um conjunto, selecione com `query_data(dataset=logger_performance)` ou use
`logger_fleet_dashboard` para o panorama. Para um aparelho, combine as dimensões
necessárias de `logger_health`, `logger_performance_detail`, `logger_battery_curve`,
`data_freshness` e `telemetry_quality`. Não execute todas para perguntas simples.

Leia [diagnostics.md](references/diagnostics.md) para hipóteses e sequências de diagnóstico;
[tools.json](references/tools.json) para limites e diferenças entre filtros;
[domain.md](references/domain.md) e [concepts.json](references/concepts.json) para objetos,
unidades e relações. Use contratos atuais, sem inventar campos ou limites operacionais.

Separe captura, chegada e cálculo. Snapshot inexistente/antigo não certifica saúde ou
defeito; dias sem observação não são percentual de coletas perdidas. Prioridade e
severidade armazenadas não são probabilidade calibrada de falha.

Apresente evidência, cobertura, hipótese e próxima verificação. Priorizar é recomendar,
não abrir ordem, reconfigurar ou reiniciar equipamento. Relacione dispositivo e ponto
pelos IDs, sem atribuir a alocação atual ao histórico inteiro.

Fotos que sustentem o diagnóstico aparecem junto ao texto. As demais vão em apêndice
visual incorporado ao documento ou galeria no chat, sem substituir imagens por links.
Leia [images.md](references/images.md) e declare qualquer falha de apresentação.
Use [client.md](references/client.md) para materialização de imagens e arquivos no cliente atual.
