# Execução no Claude

Use a conexão HydroVision autenticada e os nomes reais das tools. O cliente OAuth
configurado neste pacote é `claude-ai`, público e sem secret; escopo `vision:read`.
Não reutilize credenciais ou configuração de outro cliente. Erros de callback ou
`invalid_client` precisam de conferência do cadastro pela equipe responsável.

Para DOCX, PPTX, XLSX e PDF, utilize as capacidades de documentos e execução de código
disponíveis no Claude. Habilitação depende do cliente e do workspace. Não presuma que
outra skill esteja instalada nem use caminhos absolutos de instalações anteriores.
O modelo institucional está em `assets/templates/` na skill de relatórios. Use uma
cópia, preserve a identidade e confira os resultados com o script e o renderizador.

Mostre fotos e gráficos em blocos de imagem nativos ou referências de imagem reais
do executor, junto à interpretação. O fato de uma foto aparecer no resultado MCP
não garante acesso a seus bytes na execução de código. Declare essa limitação se
ela impedir a incorporação; não transcreva bytes pela visão nem invente links.

Incorpore evidências nos documentos; outras fotos pertinentes ficam no apêndice visual
ou em galeria na própria resposta. Anexe apenas arquivos realmente criados. Se PDF não
puder ser exportado, entregue o editável existente e explique a ausência do PDF.
