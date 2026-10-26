# Imagens integradas ao texto

## Recuperar e identificar

`logger_installation_images` retorna blocos MCP de imagem JPEG, até 1024 px no lado
maior, com ID/nome de foto. Não é necessário baixar por URL ou acessar bucket.
São até quatro arquivos por chamada. Para continuar, mantenha logger/limit e use
`page.next_offset`, mesmo quando parte dos downloads falhar. Não deduza offset pelo
número de fotos baixadas. Falha de leitura não significa ausência de fotos.

Fotos de vazamento/manômetro podem aparecer somente como metadados/URLs em detalhes.
Isso não equivale a bytes acessíveis. Use somente leitura autorizada disponível no
cliente, com origem realmente retornada pela tool; se não funcionar, registre a
indisponibilidade. Não use credenciais alternativas nem exponha URLs assinadas.

Materialize apenas conteúdo realmente exposto pelo cliente. Para blocos MCP, prefira
o recurso de arquivo/imagem do cliente; só decodifique base64 quando o payload verdadeiro
estiver acessível à execução de código. Nunca transcreva ou reconstrua bytes pela visão.
Ver uma imagem no resultado da tool não garante que o executor receba os mesmos bytes.

Associe cada evidência a tool, tipo/ID do objeto, ID da imagem, legenda e arquivo local.
Preserve datas/localização apenas quando fornecidas. Registre SHA-256 dos arquivos
materializados. A versão 1024 px é uma prévia; não a descreva como original integral.

## Compor

Posicione a figura principal imediatamente antes/depois do parágrafo que a interpreta.
A legenda deve identificar objeto e evidência, por exemplo: “Logger <MAC>, foto <ID>:
instalação observada”. Distinga observação visual de medição e hipótese.
Inclua as demais fotos pertinentes no apêndice visual do documento. Sem documento,
apresente uma galeria na própria resposta, paginando em blocos se necessário e deixando
claro o que ainda falta. Não carregue fotos sem relação com a análise.

No chat, use blocos de imagem nativos ou a sintaxe de imagem suportada com referência
de arquivo efetivamente criada pelo cliente. Um link comum para uma foto não satisfaz
a entrega. Gráficos e mapas também devem aparecer incorporados, com interpretação.

Nos documentos, incorpore bytes: DOCX com desenho inline, PPTX com imagem do slide,
XLSX com desenho ancorado à planilha, PDF com imagem renderizada. Preserve proporção,
nitidez e legenda. Evite imagens que dependam de relação externa ou URL temporária.
Não imprima base64 ou apresente nomes de arquivo como substituto da figura.

## Conferir

Compare a lista de evidências com imagens realmente incorporadas, incluindo apêndice.
Confira nomes/IDs, proporção, cortes e legibilidade na renderização de cada formato.
Abra o documento sem rede quando possível. O validador estrutural detecta mídia externa
e imagens não incorporadas, mas não comprova a apresentação no chat nem a qualidade visual.

Se bytes ou renderização não estiverem disponíveis, diga qual evidência ficou
indisponível. Não fabrique URLs, anexos ou uma entrega visual completa. Se a imagem for
essencial à conclusão, mantenha a conclusão pendente dessa evidência.
