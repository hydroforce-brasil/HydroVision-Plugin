# Execução no ChatGPT

Use a conexão HydroVision autenticada disponível na sessão, com os nomes reais das
tools. O pacote portátil declara OAuth público com client ID `chatgpt`, sem secret,
e escopo `vision:read`. Endpoints vêm de discovery. Callback precisa coincidir com o
cadastro real; não assuma que o callback de outro cliente seja válido. Não modifique
o servidor ou permissões para contornar `invalid_client` ou acesso negado.

## Arquivos e documentos

Use as capacidades disponíveis de execução de código e criação de arquivos. Confira
quais bibliotecas de documentos, planilhas, gráficos e conversão realmente existem no
executor; não dependa de skills nativas ou caminhos de outro produto. Recursos de
Pages/Canvas só são usados quando disponíveis e adequados; não substituem um DOCX/PPTX
editável quando esse for o formato solicitado. O modelo institucional já está em
`assets/templates/` na skill de relatórios; D: não precisa existir no executor.

Gere o arquivo real, confira seu conteúdo e execute o validador incorporado quando
houver execução Python. Preserve fotos, tabelas, fontes e cores do modelo. Use PNGs
de gráficos/mapas como alternativa a visuais interativos nos documentos. Sem capacidade
de converter para PDF, entregue o editável existente e indique a limitação; não renomeie
a extensão ou afirme ter anexado um arquivo inexistente.

## Imagens no chat e nos arquivos

Prefira blocos de imagem nativos. Se os bytes do resultado MCP estiverem acessíveis ao
executor, salve um arquivo real e use a referência de imagem suportada pelo ChatGPT,
junto ao parágrafo correspondente. Por exemplo, somente quando o arquivo existir e
o cliente expuser esse caminho: `![Legenda](sandbox:/mnt/data/foto.jpg)`.
Isso é incorporação de imagem; um link Markdown comum não satisfaz a apresentação.
Não invente caminhos `sandbox:`, URLs de bucket ou downloads a partir de `hydrovision://`.

Ver a imagem no retorno da tool não garante acesso aos bytes pela ferramenta de código.
Se o transporte não os expuser, declare a evidência indisponível para incorporação;
não use uma fotografia diferente ou uma reconstrução. Inclua as principais no texto e
as demais em apêndice visual incorporado ou galeria na própria resposta. Documentos
devem conter mídia interna, sem depender de URLs temporárias.

Disponibilize anexos pelos recursos reais do ambiente. Uma referência `sandbox:` só
vale na sessão que criou o arquivo e não é um link público permanente. A validação
estrutural não comprova renderização no chat: confira imagens e documentos no cliente.
