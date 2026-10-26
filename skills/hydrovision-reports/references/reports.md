# Produção e conferência de documentos

## Dados antes do layout

Escolha público em [report-profiles.json](report-profiles.json), consulte as tools
necessárias e mantenha contexto em [analysis-context.schema.json](analysis-context.schema.json).
Cada indicador preserva seu próprio recorte; o contexto geral não substitui o recorte
de um bloco que ignore período/geografia. Não recalcule regras que o backend já fornece.

Use nomes/IDs resolvidos. Exemplos de perguntas: “Relatório gerencial da empresa selecionada
para setembro”; “Diagnóstico técnico deste MAC com fotos”; “Apresentação dos resultados
e pendências”; “Planilha dos vazamentos confirmados no mês”. Desambigue empresa, evento
ou variante apenas quando a diferença mudar o resultado.

Registre população completa/parcial, paginação, cobertura e avisos. Arquivo incompleto
deve ser identificado; não anuncie como relatório completo. Não inclua informações de
outra empresa ou dados pessoais sem necessidade para o pedido.

## DOCX

Abra uma cópia de `assets/templates/institutional-document.docx` com os recursos de
edição disponíveis no cliente. Preserve capa, estilos, logos, cabeçalhos, rodapés e seções, adaptando
os blocos do roteiro ao conteúdo. Atualize título, empresa, datas, autor conhecido,+controle de versão e sumário. Remova textos de instrução, campos não preenchidos e
exemplos do modelo. Não invente aprovador, autor ou classificação diferente da existente.

Mantenha tabelas/texto editáveis. Insira fotos e gráficos como imagens inline com
proporção preservada, junto à interpretação; inclua outras fotos no apêndice visual.
Não use imagens externas que dependam de conexão. Recalcule sumário/campos quando o
cliente permitir e confira a paginação renderizada.

## PPTX

Use a variante solicitada. Se não houver escolha, pergunte clara ou escura: há dois
modelos compatíveis. Edite uma cópia do PPTX, preservando masters, tema e composições;
use os slides existentes como layouts. Remova slides de instruções e conteúdos ilustrativos.
Adapte a quantidade de slides ao público e à densidade, mantendo os blocos do roteiro.

Títulos e tabelas devem permanecer editáveis. Gráficos podem ser nativos ou imagens
incorporadas, desde que legíveis e acompanhados de unidade/fonte. Evidências principais
ficam no slide que descreve o achado; demais imagens em slides de apêndice visual.
Não coloque fotos somente em notas, referências ou hyperlinks.

## PDF

Exporte a composição DOCX/PPTX conforme os recursos disponíveis, sem trocar o layout
institucional por um PDF genérico. Se o cliente não conseguir converter, entregue o
editável realmente produzido e explique a ausência do PDF. Não renomeie a extensão.
Confira páginas, imagens, fontes, cortes e legendas na renderização. Links assinados
não são evidência incorporada e não devem sustentar um PDF de arquivo.

## XLSX

Como não há XLSX institucional de origem, derive a identidade documentada em
[branding.md](branding.md). Use abas Contexto, Indicadores, Dados e Evidências, criando
abas de dados por entidade quando isso melhorar a leitura. Registre empresa, período,+evento, unidades, fórmulas adicionais, cobertura e atualização.

Mantenha IDs, MACs e códigos como texto quando necessário, preservando zeros à esquerda.
Valores numéricos devem ser células numéricas, sem transformar desconhecidos em zero.
Congele cabeçalhos, configure filtros e área de impressão. Coloque gráficos/imagens
na planilha junto à explicação e organize as demais fotos na aba Evidências.
Ao importar texto não confiável, escreva como texto explícito; não transforme conteúdo
de células CSV em fórmula. Fórmulas são apenas as intencionalmente criadas na análise.

## CSV original e versões derivadas

O MCP entrega recursos `text/csv`, não URLs públicas. Materialize o conteúdo original
sem reconstruí-lo a partir da prévia. Ele já contém BOM; codifique em UTF-8 sem duplicar.
Preserve `;`, aspas, CRLF, zeros à esquerda, tamanho e SHA-256. Use leitor CSV real
com `utf-8-sig`, não split de linhas/células. Analise o arquivo completo.

Os mensais incluem arquivados e primeiro endereço. `unrepaired` = confirmação no mês,
sem reparo em qualquer data; `repaired` = confirmação e reparo no mesmo mês. Não são
todos os reparos do mês ou estoque histórico. Limites: 5000 linhas / 256 KiB por arquivo,
1 MiB no envelope; erro não retorna arquivo parcial. Divisões devem ser disjuntas e
declaradas. XLSX e relatório são derivados; não substituem o CSV original.

## Gate de entrega

1. Execute `python scripts/validate_delivery.py ARQUIVO --context CONTEXTO.json` com o
   contexto usado na geração. Para verificar CSV original, acrescente metadados reais
   com `--csv-sha256 HASH --csv-bytes TAMANHO --csv-rows LINHAS`.
2. Corrija erros estruturais, referências externas a imagens, imagens faltantes e
   campos de modelo não substituídos. Se transformar bytes de uma figura, registre o
   hash do arquivo final incorporado no contexto, mantendo a fonte original identificada.
3. Renderize e inspecione todas as páginas/slides/abas pertinentes. O validador não
   mede sobreposição, legibilidade, posição semântica da figura nem renderização do chat.
4. Confira valores/unidades entre os formatos, identificação das evidências e os
   avisos de cobertura. Abra sem rede quando possível. Não anuncie “validado no cliente”
   apenas porque um script local passou.
5. Mostre um resumo com figuras integradas e anexe somente os arquivos existentes.
