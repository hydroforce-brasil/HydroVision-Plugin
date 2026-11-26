# Contagens, médias e agregação estatística

Um número do HydroVision só se sustenta com três coisas ao lado: a população de onde
saiu, o denominador e a cobertura. Este guia mostra como obter cada medida com o mínimo
de chamadas e como não errar a conta. Os schemas atuais das tools prevalecem sobre os
nomes citados aqui.

## O que o servidor já calcula

`query_data` com `dataset=leaks` e `mode=aggregate` calcula sobre toda a população
filtrada, antes de qualquer paginação. É o caminho para totais, médias e séries de
vazamentos; páginas de registros não servem para isso.

| Métrica | Unidade | Definição |
|---|---|---|
| `count` | vazamentos | Casos únicos na população filtrada. |
| `estimated_flow_total_m3_per_day` | m³/dia | Soma das vazões estimadas; nulo se nenhuma existir. Inclui reparados, a menos que `current_status` filtre. |
| `estimated_flow_mean_m3_per_day` | m³/dia | Média das vazões estimadas, só nos casos que têm estimativa; nulo se nenhuma existir. |
| `with_flow_estimate_count` | vazamentos | Casos com estimativa armazenada, inclusive zero. |
| `repair_duration_mean_days` | dias | Média da primeira confirmação ao primeiro reparo, só nos casos elegíveis. |
| `repair_duration_median_days` | dias | Mediana das mesmas durações. |
| `repair_duration_count` | vazamentos | Casos elegíveis: primeiro reparo na data da confirmação ou depois dela. |

`group_by` aceita até três entre `company_id`, `sector_id`, `leak_type`, `leak_position`,
`pipe_material`, `pipe_diameter` e `month`. Exemplo, vazamentos confirmados por mês em
doze meses completos (início inclusivo, fim exclusivo):

```json
{"dataset": "leaks", "mode": "aggregate", "company_ids": [ID_DA_EMPRESA],
 "metrics": ["count"], "group_by": ["month"],
 "period": {"start": "2025-11-01", "end": "2026-11-01", "basis": "confirmed_at"}}
```

Como ler a resposta:

- `data.totals` é a população inteira do recorte. O número principal sai daqui.
- `data.rows` traz um grupo por linha, paginado; `page.total` é a quantidade de grupos.
  Somar uma página de grupos não reconstrói o total.
- `coverage` sempre traz `count` e `with_flow_estimate_count`, e `repair_duration_count`
  quando há métrica de duração. São os denominadores e a cobertura da população inteira.
- Com `group_by`, peça também a métrica de contagem (`count` ou `repair_duration_count`):
  o n de cada grupo só vem se for pedido, e sem ele não dá para saber que a média de um
  setor saiu de um único caso.
- Grupo sem vazamento não aparece. Em contagens, mês ou setor ausente é zero, não lacuna.
- Grupos por `sector_id` trazem também `sector_name`. Outros IDs se traduzem em uma
  única consulta com `filters.ids`; não resolva um por um.
- Se o schema da tool não listar uma métrica ou um modo citado aqui, o servidor é de
  versão anterior: calcule a vazão média como soma ÷ `with_flow_estimate_count`, busque
  os nomes dos setores em `sectors` e conte os demais datasets por `page.total`.
- `month` exige `period` e agrupa pelo mês do evento da `basis`. Métricas de duração
  exigem `basis=repaired_at` ou nenhum período.
- Ranking: `order_by` por uma métrica selecionada e `limit` do tamanho pedido. O total
  continua em `data.totals`, para dizer quanto do todo o ranking representa.

## Médias e seus denominadores

"Média" pede sempre numerador, denominador e população. As leituras usuais:

| Medida | Como calcular | Informe junto |
|---|---|---|
| Vazamentos por mês | `count` do período ÷ meses completos do período | Período, evento da data e quantos meses entraram |
| Vazão média por vazamento | `estimated_flow_mean_m3_per_day`, igual à soma ÷ `with_flow_estimate_count` | Cobertura: casos com estimativa sobre o total |
| Tempo até o reparo | `repair_duration_mean_days`, com a mediana ao lado | `repair_duration_count` como n |
| Vazamentos por setor | `count` ÷ número de setores | Qual denominador: setores com vazamento (`page.total` dos grupos) ou todos os setores da empresa |
| Participação de um grupo | grupo ÷ `data.totals` da mesma consulta | O total usado como base |

Regras que evitam os erros mais comuns:

- **Média de médias não é a média.** A média geral sai de `data.totals` ou de soma ÷
  contagem. Tirar a média das médias dos grupos dá o mesmo peso a um setor com 2 casos
  e a outro com 200.
- **Mediana não se combina.** Não há como obter a mediana geral a partir das medianas
  dos grupos; peça a métrica para a população exata que a pergunta descreve.
- **Durações são assimétricas.** Poucos reparos muito demorados puxam a média. Mostre
  média e mediana juntas e diga qual descreve o caso típico.
- **Nulo fica fora, zero entra.** Vazão sem estimativa é desconhecida: sai do
  denominador e aparece na cobertura. Estimativa zero conta como medida.
- **Mês sem linha é zero.** Na média mensal, divida pelos meses do período, não pela
  quantidade de linhas devolvidas. Deixe o mês corrente, ainda parcial, fora da média
  ou identifique-o.
- **Estoque não é fluxo.** "Em aberto hoje" é estado atual, sem período (`repair_backlog`
  ou filtro `current_status`). "Confirmados em outubro" é evento no período. O estado
  atual não reconstrói o estoque de uma data passada; por isso estes dados não dão uma
  "média de vazamentos em aberto por mês".
- **Casos não são eventos.** `leak_summary` conta eventos de situação e repete o mesmo
  vazamento; não o misture com contagens de `query_data` na mesma conta.
- **Poucos casos, pouca média.** Informe n sempre. Com um punhado de casos, liste os
  valores em vez de resumi-los em uma média.
- **Variação percentual** vem de `compare_metrics`, com a mesma `basis` nos dois lados.
  Base zero não tem percentual. Janelas de durações diferentes precisam ser normalizadas
  por dia ou por mês, e a resposta deve dizer que foram.

## Quando o servidor não agrega

Somas, médias e medianas existem só para vazamentos. Para os demais dados:

- **Contagem por grupo é uma chamada.** `loggers`, `logger_performance` e
  `investigations` aceitam `mode=aggregate` com `metrics=[count]` e `group_by`: status,
  setor, modelo e firmware nos loggers; status, modo de criação e mês do período nas
  investigações. Os filtros do dataset valem, então "offline por setor" é o filtro
  `offline` com `group_by=[sector_id]`.
- **Estado da frota é uma chamada.** `logger_fleet_dashboard` devolve, para a empresa
  selecionada, o total de loggers instalados e quantos estão offline, saudáveis, em
  atenção ou críticos, além das contagens por sintoma e das faixas de bateria. Já vem
  com a base do percentual; prefira-o a contar pelo dataset.
- **Contar o resto também é uma chamada.** Toda consulta de registros devolve
  `page.total`, a contagem exata do recorte filtrado. Use `limit=1` e leia `page.total`;
  não percorra as páginas para contar. Vale para loggers, indicadores de desempenho,
  setores, usuários, pontos de medição e investigações. Para um percentual, a base é a
  mesma consulta sem o filtro da condição.
- **O inventário de loggers inclui todos os status de instalação**, e aparelho em
  estoque também consta como sem comunicação. Em contagens pelo dataset, filtre
  `status_ids` pelo status de aparelho instalado (`Ativo`; a lista vem em
  `describe_data`) quando a pergunta for sobre o parque em campo.
- **Veja se um panorama já traz o agregado** antes de paginar: `sector_summary` para
  setores, `dashboard_management` para a visão gerencial e o trabalho de campo,
  `repair_backlog` para o estoque em aberto. Cada bloco tem recorte próprio; não o force
  ao período da pergunta.
- **Estatística que nenhuma tool entrega** (média de bateria, percentis, distribuição de
  um campo, soma de rede varrida): busque todas as páginas pedindo só os campos da
  conta, com `limit=200`, e calcule com execução de código, não de cabeça nem contando
  texto. Informe n, quantos nulos ficaram fora e a fórmula. Sem execução de código,
  fique no que o servidor agrega e diga o que ficou de fora.
- **Se não der para completar** (`limit_reached`, `truncated`, cursor expirado, limite
  de 10.000 registros), estreite o recorte ou apresente o resultado como parcial. Não
  extrapole uma página para a população. As páginas não são um instantâneo: os dados
  podem mudar entre uma e outra.

## Apresentar o número

Comece pelo número, com unidade. Em seguida, uma linha de recorte: empresa, período com
o evento da data, n e cobertura. Depois, só a ressalva que muda a leitura. Modelo, com
valores ilustrativos:

> Tempo médio até o reparo: 6,4 dias (mediana 3,0), em 212 vazamentos reparados.
> Empresa Exemplo, reparos de 1 a 31 de outubro de 2026.

Mostre o período como o usuário o leria (1 a 31 de outubro), ainda que o argumento use
fim exclusivo. Formate em pt-BR só na apresentação e não exiba mais casas do que o dado
sustenta: uma casa decimal costuma bastar. Diga o que foi presumido no recorte. Encerre
oferecendo, em uma linha, o próximo corte que faria sentido (por setor, por mês,
comparação com o período anterior), sem executá-lo antes de o usuário pedir.
