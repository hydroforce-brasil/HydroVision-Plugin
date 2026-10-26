# Escolha e preparação de visualizações

Leia [views.json](views.json) para equivalências com as telas e
[images.md](images.md) para incorporação no texto e nos documentos.

| Pergunta | Representação |
|---|---|
| Quanto e em qual recorte? | Indicador com unidade, denominador/cobertura e data de referência. |
| Como evoluiu? | Linha ou barras por período; marcar mês corrente parcial e lacunas. |
| Quais setores/casos priorizar? | Barras horizontais ordenadas ou tabela; critério explícito. |
| Quais estados/tipos predominam? | Barras com casos únicos ou eventos identificados; evitar misturar contagens. |
| Como se relacionam os objetos? | Diagrama com nomes canônicos e cardinalidades; distinguir vínculo atual de histórico. |
| Onde estão casos/evidências? | Mapa com coordenadas realmente retornadas; eixo/projeção coerentes. |
| Qual a saúde e atualização? | Painel de dimensões com horários de captura, chegada e cálculo separados. |
| Qual a sequência do caso? | Linha do tempo com eventos disponíveis e estado atual identificado. |

Prefira gráficos estáticos incorporáveis para relatórios e imagens PNG de boa resolução.
Um visual interativo pode complementar a análise no cliente, mas precisa de equivalente
estático quando solicitado em documento. Use os valores numéricos brutos nos cálculos;
formate pt-BR apenas na apresentação. Não converta `4.980` formatado de volta com `float`.

Identifique eixos, unidade, fonte, escopo, base temporal e lacunas. Ordenação/corte devem
ser explícitos. Se exibir top N, preserve total e cobertura calculados sobre a população
correta. Não desenhe zero em amostra ausente ou use gráfico suave para inventar medições.

Mapas: GeoJSON usa longitude/latitude, e não a ordem inversa. Rejeite coordenadas inválidas;
não substitua posição desconhecida por (0,0). Sem base cartográfica autorizada disponível,
mostre coordenadas em diagrama geográfico identificado como tal. Não prometa malha viária.
`sector_summary` não entrega limites/tubulação/loggers instalados; `timeline` força
`include_points=false`. Use polígonos/centroides somente quando presentes nas respostas.
ID de cluster não identifica um local permanente.

O nome “Economia projetada” e a unidade m³/ano devem sobreviver à exportação. Não rebatize
a série como volume mensal recuperado. Campo e ranking podem ignorar filtros do seletor:
reproduza seus recortes reais nas legendas, sem forçar todos os gráficos ao mesmo período.
