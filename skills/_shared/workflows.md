# Análises e consultas do HydroVision

Transforme a pergunta do usuário em consultas com escopo definido e uma resposta útil,
desde uma busca simples até um relatório com várias fontes. As ferramentas HydroVision
são somente leitura; gerar um arquivo no cliente não altera o sistema.
Use as ferramentas da conexão HydroVision disponível: o prefixo dos nomes pode variar
entre clientes. Seus schemas, descrições e metadados retornados são a referência atual;
este guia orienta o trabalho, sem substituir as regras calculadas pelo backend.

## Definir o recorte

- Consulte `get_context` no início ou quando mudar a organização. Reaproveite o contexto
  válido; uma pergunta simples não exige repetir toda a descoberta.
- Use a empresa e os filtros pedidos. Se o usuário não indicar empresa, a selecionada pode
  servir como padrão, deixando isso claro. Não amplie para todas as empresas autorizadas.
- Resolva nomes, MACs, endereços e códigos com `resolve_entities`. Se houver candidatos
  incompatíveis com a mesma descrição, peça a distinção necessária antes da consulta.
- Para perguntas temporais, defina período, fuso e evento: confirmação, reparo, captura,
  abertura etc. Converta datas relativas em datas explícitas. Pergunte quando a ambiguidade
  mudar o resultado; aproveite informações já estabelecidas na conversa.
- Use `describe_data` antes de construir uma consulta cujo contrato ainda não conhece.
  Consulte campos, filtros, unidades e definições disponíveis; não invente SQL ou parâmetros.

## Escolher as ferramentas

Use o caminho mais curto que responda à pergunta. Aprofunde só os casos relevantes; não
execute o catálogo inteiro para cada análise. Para novas ferramentas, aplique o mesmo
processo lendo sua descrição e seu schema antes de chamar.

| Necessidade | Caminho preferido |
|---|---|
| Selecionar cadastros ou registros | `query_data` com o dataset apropriado: empresas, setores, loggers, usuários, pontos, vazamentos, indicadores ou investigações. Peça só os campos necessários. |
| Totais e agrupamentos de vazamentos | `query_data` com `mode=aggregate`; use métricas do backend para a população completa. |
| Comparar períodos, setores ou empresas | `compare_metrics` para métricas de vazamentos; para outros dados, consulte recortes equivalentes e explicite o cálculo adicional. |
| Priorizar reparos e investigar um caso | `repair_backlog` com critério explícito e `leak_detail` para aprofundar. Prioridade é uma recomendação, não uma ordem de serviço executada. |
| Panorama gerencial ou de um setor | `dashboard_management`, `dashboard_volume_series` e `sector_summary`; confira o recorte de cada bloco antes de combinar números. |
| Parque de loggers e diagnóstico | `logger_fleet_dashboard` para o conjunto; `query_data` em `logger_performance` para selecionar aparelhos; `logger_performance_detail`, `logger_health` e `logger_battery_curve` para aprofundar. |
| Atualização e qualidade dos dados | `data_freshness` para captura, chegada e cálculo; `telemetry_quality` para observação, valores ausentes/inválidos e atrasos. |
| Localização e recorrência espacial | `leak_hotspots_timeline` para os quadros e `leak_hotspots_summary` para o intervalo. |
| Trabalho de campo | `query_data` em `investigations`, `investigation_detail` e `field_sessions_live`, conforme busca, detalhe ou sessões em andamento. |
| Utilização de pontos para faturamento | `measurement_point_billing`, respeitando a unidade, o período e as regras retornadas. |
| Fotos de instalação | `logger_installation_images`, depois a apresentação visual descrita abaixo. |
| CSVs mensais dos scripts de vazamentos | `export_monthly_leaks`; confira a regra específica de seleção antes de usar em outra análise. |

Prefira `query_data` às listagens legadas para seleção paginada. `leak_search` é um atalho
de compatibilidade; `leak_list`, `logger_performance_list` e `investigation_list` ainda
podem atender campos ou filtros específicos. `leak_summary` conta eventos, não casos únicos.

## Consultar e combinar dados

- Filtre e agregue no servidor antes de buscar detalhes. Faça uma seleção em lote em vez
  de uma chamada por registro quando a ferramenta suportar isso. Reutilize dados já obtidos
  se ainda atenderem ao recorte e à atualização exigidos pelo pedido.
- Nas ferramentas analíticas, continue com `page.next_cursor` e os demais argumentos iguais.
  Uma primeira página ou resultado `truncated` não é uma base completa. Para totais, prefira
  agregações; se precisar calcular no cliente, obtenha todas as páginas necessárias ou
  identifique o resultado como parcial, sem extrapolar. As páginas não são um snapshot único.
- Cruze resultados por IDs e relações fornecidas, preservando empresa e período. Confira a
  cardinalidade para não duplicar vazamentos ao juntar fotos, eventos ou participações.
  Coincidência de endereço, setor ou proximidade espacial não comprova uma relação.
- Use as regras e métricas devolvidas pelo backend. Cálculos adicionais devem informar sua
  fórmula, unidade e população. Para cálculos extensos ou processamento de arquivos, use
  execução de código disponível no cliente; não estime totais contando texto manualmente.
- Leia `scope`, `period`, `method`, `coverage`, `warnings` e paginação quando presentes.
  Nulo significa desconhecido ou não aplicável, não zero. Ao avaliar um indicador suspeito,
  confira atualização e cobertura antes de concluir que houve falha operacional.
- Preserve a distinção entre resposta vazia, acesso negado, ferramenta indisponível e erro.
  Corrija parâmetros inválidos ou reduza consultas grandes de forma explícita; não repita
  chamadas idênticas indefinidamente. Se faltar capacidade no catálogo, diga qual dado ou
  operação faltou, sem afirmar que o restante do relatório está completo.

## Interpretar sem misturar conceitos

- Períodos analíticos têm início inclusivo e fim exclusivo. Use o fuso retornado e o formato
  de cada ferramenta; algumas rotas REST pedem `dd/MM/yyyy`. Estado atual não é histórico
  no fim do período. Em `query_data` para vazamentos, datas de eventos são primeiras ocorrências;
  durações não reconstroem ciclos de reabertura.
- Compare populações com filtros, unidades e base temporal equivalentes. Janelas de durações
  diferentes exigem ressalva; taxas adicionais precisam de denominador explícito. Base zero
  não permite variação percentual. Informe cobertura quando houver estimativas ausentes.
- Volume projetado não é volume medido: a série gerencial distribui por mês contribuições
  anuais dos reparos, em m³/ano. Os blocos da dashboard podem usar recortes diferentes.
- `repair_backlog` representa estoque atual. Cluster acústico é uma sugestão, não vazamento
  confirmado; seu ID muda a cada execução. Para mapa atual, use a linha do tempo com `days=1`;
  para recorrência, o resumo espacial. Não conte IDs de clusters como locais únicos.
- Snapshot ausente não comprova equipamento saudável ou defeituoso. Captura, chegada e
  atualização de indicadores são tempos distintos. `telemetry_quality` usa 1–31 dias
  completos; dias sem observação não são coletas perdidas sem uma agenda histórica confiável.
- Os filtros de setor dos loggers usam a alocação atual; não representam automaticamente
  o histórico de um ponto. Em usuários, empresa de vínculo difere de `company_scope`.

## Entregar a resposta

Responda primeiro à pergunta, com a profundidade pedida. Uma consulta simples pode ter uma
resposta curta; análises maiores podem combinar resumo, tabela, gráfico e arquivo.
Indique escopo, período, unidades e limitações que afetem a conclusão. Vincule os achados
aos nomes/IDs e às ferramentas usadas, sem despejar JSON ou inventar links para o sistema.
Distinga constatação, estimativa e hipótese; uma recomendação deve apontar a evidência.

Use tabelas para registros e comparações; gráficos para tendências ou distribuições quando
ajudarem a responder. Identifique eixos, unidades e séries incompletas. Não preencha lacunas
como zero nem suavize valores sem explicar. Um relatório pode incluir fotos relevantes e
anexos; não precisa consultar imagens ou gerar arquivos em toda resposta.
Se o usuário pedir um documento, gere-o com as ferramentas de arquivo disponíveis no cliente
e verifique o conteúdo antes de anunciar o anexo. A ferramenta MCP fornece os dados; a
capacidade de montar e apresentar o documento depende do cliente.

### Fotos no chat e em relatórios

`logger_installation_images` entrega as imagens no próprio resultado, em JPEG de até 1024
pixels no lado maior, acompanhadas de ID e nome do arquivo. Ao pedir fotos, mostre-as no
chat sempre que a interface permitir, com legenda identificando logger e foto. Não entregue
só o nome ou um link quando puder apresentar a imagem. Não é necessário buscar o bucket.

Para incluir uma foto em um relatório, reutilize o conteúdo recebido com os recursos de
arquivos do cliente, preserve a proporção e mantenha a legenda. Essas são versões reduzidas:
não as descreva como originais em resolução plena. Diferencie o que a imagem permite observar
do que depende de medição ou inspeção de campo. Não atribua data ou localização sem metadados.

São até quatro fotos por chamada. Quando necessário, prossiga com `offset=page.next_offset`
e o mesmo `id`/`limit`; não derive o próximo offset da quantidade de downloads bem-sucedidos.
Avise sobre falhas parciais sem declarar que as fotos não existem. Nunca imprima base64 nem
invente URLs para incorporá-las. Se o cliente não expuser a imagem para apresentação ou
inclusão no documento, informe essa limitação específica.

### CSVs e relatórios mensais

`export_monthly_leaks` recebe uma empresa, mês e ano; pode devolver os dois relatórios ou
apenas o solicitado. A seleção reproduz os scripts:

- `unrepaired`: confirmado no mês e sem nenhum reparo em qualquer data.
- `repaired`: confirmado e reparado no mesmo mês, com o primeiro evento de cada tipo dentro dele.

Inclui arquivados e primeiro endereço cadastrado. Esses grupos não formam uma partição de
todas as confirmações, não abrangem todos os reparos do mês e não representam estoque ao
fim do mês. Por exemplo, confirmação em setembro e reparo em outubro excluem o caso dos
dois arquivos de setembro. Para outras perguntas, use o recorte apropriado em `query_data`.

Os arquivos completos vêm em recursos embutidos `text/csv`; os metadados informam nome,
linhas, tamanho e SHA-256. Use o conteúdo recebido, não reconstrua o original a partir de
uma lista ou da prévia. Preserve BOM UTF-8, separador `;`, aspas, quebras de linha e valores.
Se materializar o texto embutido em arquivo, ele já contém o BOM: codifique em UTF-8 sem
adicionar outro. Quando possível, confira o tamanho e o SHA-256 informados.

Carregue o CSV com um leitor apropriado (`utf-8-sig`, separador `;`) se houver execução de
código disponível; não divida linhas ou células manualmente, pois podem conter aspas e
quebras internas. Preserve identificadores e zeros à esquerda. Mostre uma prévia tabular
no chat, identificada como prévia, com a quantidade total de registros, e disponibilize o
arquivo completo pelos recursos de anexos do cliente. Se o usuário pedir análise, calcule
sobre todo o arquivo, não só sobre as linhas exibidas. Arquivo vazio ainda tem cabeçalho.

Mantenha o CSV original separado de planilhas, gráficos ou relatórios derivados. O URI
`hydrovision://` identifica o recurso; não é uma URL pública nem um link de download. Use
somente referências de arquivos efetivamente criados pelo cliente. Se apenas os metadados
estiverem acessíveis, não invente prévia ou linhas; informe a limitação de acesso ao conteúdo.

O limite é de 5.000 registros e 256 KiB por arquivo. Em erro, restrinja setores de acordo
com o pedido e identifique o recorte; se precisar dividir, mantenha partes sem sobreposição.
Não apresente uma parte como relatório completo. Pedir apenas um tipo reduz o envelope,
mas não o limite individual. Em erro de limite, a ferramenta não entrega arquivo parcial.
