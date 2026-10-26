---
name: hydrovision-reports
description: Produzir relatórios gerenciais e técnicos HydroVision em DOCX, PPTX, PDF e XLSX com modelos institucionais, dados rastreáveis e imagens incorporadas ao texto e ao apêndice visual.
---

# Documentos institucionais HydroVision

Produza arquivos quando solicitados. Use a conexão MCP autenticada para dados e as
capacidades disponíveis de criação/edição de documentos do cliente para o formato solicitado.
Não é necessário um servidor MCP de documentos ou acesso ao disco Windows do autor.
Leia [client.md](references/client.md) para recursos, arquivos e imagens no ambiente atual.

## Preparar a entrega

1. Confirme empresa e escopo com `get_context`; resolva objetos e leia contratos atuais.
   Consulte [domain.md](references/domain.md), [concepts.json](references/concepts.json)
   e [tools.json](references/tools.json) conforme necessário.
2. Escolha público gerencial ou técnico em [report-profiles.json](references/report-profiles.json).
   Organize dados em [analysis-context.schema.json](references/analysis-context.schema.json),
   preservando recortes distintos por indicador, fonte, cobertura e avisos.
3. Consulte [templates.json](references/templates.json) e [branding.md](references/branding.md).
   Abra o modelo incorporado em `assets/templates/`; preserve sua identidade e adapte
   conteúdo e blocos. Sem variante explícita, use a única compatível; havendo várias,
   pergunte clara/escura. Apresentações de exemplo são referências, não assets disponíveis.
4. Siga [reports.md](references/reports.md) para formatos, composição, fontes e conferência.
   Use [views.json](references/views.json) para selecionar visuais e
   [images.md](references/images.md) para obter, materializar e incorporar imagens.
5. Valide os arquivos com `python scripts/validate_delivery.py ARQUIVO --context CONTEXTO.json`.
   Inspecione também as páginas/slides renderizados. O script não certifica layout nem
   renderização no chat; PDF requer inspeção visual e, quando disponível, PyMuPDF.

## Imagens e entrega

Cada foto/gráfico principal aparece junto ao texto que sustenta; demais fotos ficam em
apêndice visual incorporado. No chat, mostre as principais junto ao resumo e as demais
em galeria quando não houver documento. Nunca substitua imagem por link, redirecionamento,
nome ou base64. Não use endereços assinados como mídia externa no arquivo.

Sem acesso aos bytes ou ao renderizador, registre a limitação e não declare entrega
visual completa. Dados ausentes devem permanecer identificados; não fabrique medições,
fotografias, gráficos, mapas ou conclusões para completar o modelo.

Sem formato indicado: relatório = DOCX + PDF; apresentação = PPTX + PDF; planilha = XLSX.
Um formato pedido explicitamente prevalece. Preserve os CSVs originais em separado e
disponibilize apenas anexos realmente produzidos e conferidos.
