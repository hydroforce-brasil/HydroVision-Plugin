---
name: hydrovision-analysis
description: Usar em toda pergunta sobre dados do HydroVision (quantos, média, total, ranking, evolução, comparação) de vazamentos, setores, loggers, usuários e investigações, antes de chamar as tools.
---

# Análises do HydroVision

Responda à pergunta com as tools da conexão HydroVision disponível. Elas são somente
leitura. O prefixo varia entre clientes; schemas atuais e metadados das respostas
prevalecem sobre os exemplos desta skill.

## Pré-voo: fechar a pergunta antes de consultar

Antes da primeira tool, escreva para si a pergunta em uma frase com quatro partes:
**medida** (o que se conta, soma ou tira a média), **população** (quais registros),
**recorte** (empresa, setor, período e o evento que data o período) e **forma** (um
número, uma tabela, uma série). O plano de chamadas sai dessa frase. Sem ela, a
tendência é consultar várias tools e devolver números que não se comparam entre si.

- **Recorte faltando: presuma e declare.** Sem empresa, use a selecionada em
  `get_context`; não amplie para todas as autorizadas. Sem período, use o estado atual
  para perguntas de estoque ("quantos em aberto", "quantos loggers offline") e os
  últimos 12 meses completos para todas as outras: contagem de eventos, médias de
  qualquer tipo e evolução. "Vazamentos em outubro" são os confirmados em outubro
  (`basis=confirmed_at`); "reparados" usa `repaired_at`. Converta datas relativas em
  datas explícitas.
- **Medida ambígua: pergunte uma vez, antes de consultar.** Se leituras diferentes dão
  números diferentes, faça uma pergunta curta com duas a quatro opções concretas, a
  recomendada primeiro. Não execute todas as leituras para o usuário escolher depois.
- **Pergunta fechada: consulte direto.** Não peça confirmação do que já foi dito na
  conversa nem do que tem padrão acima.

"Qual a média dos vazamentos?" é ambígua na medida: pode ser vazamentos confirmados por
mês, vazão estimada por vazamento ou tempo até o reparo. Pergunte qual. "Quantos
vazamentos tivemos em outubro?" está fechada: confirmados em outubro, empresa
selecionada, uma agregação.

## Consultar com o mínimo de chamadas

Uma pergunta de número custa, em regra, `get_context` (uma vez por conversa) e uma
chamada. Se o plano passar de três chamadas para uma pergunta simples, volte ao pré-voo.

| Pergunta | Chamada | Onde está a resposta |
|---|---|---|
| Quantos vazamentos, vazão total | `query_data` com `dataset=leaks`, `mode=aggregate` e `metrics` | `data.totals` |
| Por setor, tipo, material, diâmetro ou mês; ranking | a mesma, com `group_by` (até 3), `order_by` e `limit` | `data.rows`; total em `data.totals` |
| Vazamentos por mês, em média | `metrics=[count]`, `group_by=[month]` e `period` | total ÷ meses do período |
| Vazão média por vazamento | `metrics=[estimated_flow_mean_m3_per_day]` | `data.totals`; cobertura em `coverage.with_flow_estimate_count` |
| Tempo médio ou mediano até o reparo | `repair_duration_mean_days`, `repair_duration_median_days` e `repair_duration_count` | `data.totals`; com `group_by`, o n de cada grupo é a métrica de contagem |
| Antes e depois, um recorte contra outro | `compare_metrics` | `data.rows` |
| Em aberto hoje | `repair_backlog` | `data.totals` |
| Frota instalada hoje: offline, bateria baixa, saudáveis | `logger_fleet_dashboard` (empresa selecionada) | contagens e `total_installed`, que serve de base do percentual |
| Loggers ou investigações por status, setor, modelo ou mês | `query_data` com `mode=aggregate`, `metrics=[count]` e `group_by` | `data.rows`; total em `data.totals` |
| Quantos loggers, setores, usuários, pontos ou investigações em um recorte | `query_data` com filtros e `limit=1` | `page.total` |

- O servidor agrega a população inteira; não tire total nem média de uma página de
  registros. Leia [statistics.md](references/statistics.md) antes de calcular média,
  taxa, mediana ou comparação: ele traz denominadores, cobertura e os erros comuns.
- O schema de `query_data` já enumera datasets, campos, filtros, métricas e grupos.
  `describe_data` serve para tirar dúvida de definição, unidade ou limite, não como
  passo de rotina.
- O inventário de loggers inclui todos os status de instalação, e aparelho em estoque
  também consta como sem comunicação. Fora do painel da frota, filtre `status_ids` pelo
  status de aparelho instalado (`Ativo`; a lista vem em `describe_data`) quando a
  pergunta for sobre o parque em campo.
- Use `resolve_entities` só quando a pergunta citar um objeto por nome, endereço, MAC
  ou código, e desambigue candidatos incompatíveis. Não confunda conta, funcionário,
  equipamento e ponto. Grupos por setor já trazem `sector_name`; outros IDs se traduzem
  em uma única consulta filtrando `ids`, não um a um.
- Escolha uma fonte por medida. Dashboards, `leak_summary` e `query_data` usam
  definições diferentes; cruzá-los para conferir produz números que não batem. Use uma
  segunda fonte só se o usuário pedir a conciliação.
- Preserve `scope`, `period`, `method`, `coverage`, `warnings` e paginação. Quando
  precisar de todas as linhas, continue com `page.next_cursor` e os mesmos argumentos.

Leia [domain.md](references/domain.md) para conceitos e diferenças de métricas;
[concepts.json](references/concepts.json) para objetos, campos e relações;
[tools.json](references/tools.json) para selecionar uma tool;
[workflows.md](references/workflows.md) para paginação, cruzamentos, comparação e CSVs.
Carregue apenas as referências necessárias à pergunta.

## Apresentar

Responda primeiro, com o número e a unidade. Depois, uma linha com o recorte (empresa,
período e evento, n e cobertura) e o que foi presumido no pré-voo. Inclua só a ressalva
que muda a conclusão, não a lista inteira de avisos. Relacione achados a objetos
identificados e distinga observação, estimativa e hipótese. Encerre oferecendo, em uma
linha, o próximo corte útil, sem executá-lo antes do pedido.

Use nomes canônicos em português; mantenha códigos técnicos nos argumentos das tools.
Não transforme nulo em zero, uma página em total, eventos em casos ou economia projetada
em volume medido.

Imagens principais aparecem junto ao texto, com legenda e objeto de origem. As demais
ficam em apêndice visual incorporado ao documento; no chat, em galeria na própria
resposta. Não substitua imagens por links, redirecionamentos, nomes ou base64.
Leia [images.md](references/images.md) ao consultar fotos ou produzir conteúdo visual.
Se o cliente não permitir apresentar os bytes, declare a evidência indisponível;
não afirme que a imagem foi exibida ou anexada.

Arquivos são gerados quando solicitados, usando as capacidades disponíveis do cliente.
Leia [client.md](references/client.md) para autenticação, arquivos e imagens no ambiente
atual. Confirme que o arquivo existe e que o conteúdo foi verificado antes da entrega.
