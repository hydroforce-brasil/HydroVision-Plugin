# Instalar e verificar a coleção HydroVision

O build gera versões separadas para Claude e ChatGPT, com a mesma base de skills,
catálogos e modelos. Para ChatGPT, siga o [guia próprio](../docs/INSTALL-CHATGPT.md).
O guia abaixo descreve a instalação Claude. Não reutilize o Client ID de um cliente no outro.

## Plugin completo no Claude

Use `claude/hydrovision-plugin.zip` em **Personalizar / Customize → Plugins**, na opção de
upload de plugin personalizado disponível no seu cliente/workspace. O arquivo contém
`.claude-plugin/plugin.json`, `.mcp.json` e as quatro skills com todos os seus recursos.
A autenticação OAuth continua necessária; pacote e Client ID público não concedem acesso.
Se o cliente solicitar dados OAuth, use `claude-ai`, sem Client Secret, escopo `vision:read`.
Em conflito de callback/cliente, siga o guia de conexão do repositório e peça à equipe
para verificar o cadastro; não altere a autenticação do servidor para contornar o erro.

## Skills individuais no Claude.ai e Desktop

Se o cliente não oferecer upload de plugin, use os quatro ZIPs individuais em
**Personalizar / Customize → Skills → Adicionar / Upload a skill**. Habilite criação
e edição de arquivos/execução de código, além das capacidades de Word, PowerPoint,
Excel e PDF. Conecte o MCP HydroVision separadamente conforme o README principal.

Cada ZIP tem exatamente uma pasta de skill na raiz. Não envie o ZIP do plugin como
se fosse uma skill. Não instale simultaneamente versões individuais e do plugin que
dupliquem as mesmas skills. Elas não são instaladas apenas por conectar o MCP.

Os modelos e referências já estão nos pacotes; D: não precisa existir no executor do
cliente. A fonte é Python 3.10+ e o empacotador usa apenas a biblioteca padrão.

## Conferência no cliente

1. “Use o HydroVision para listar as empresas que posso consultar.” Verifique contexto.
2. “Explique a diferença entre logger, ponto de medição, conta e funcionário.” Confira nomes.
3. “Compare vazamentos de dois meses da empresa selecionada.” Confira evento, cobertura e páginas.
4. “Diagnostique este logger e mostre as fotos junto aos achados.” Confira imagem real,
   legendas, próxima página e falhas parciais.
5. “Gere relatório técnico em DOCX e PDF e uma planilha XLSX.” Abra cada arquivo, confira
   unidades, fotos no texto/apêndice e ausência de dependência de URLs externas.
6. “Crie uma apresentação gerencial.” Sem variante indicada, deve perguntar clara/escura.

Use objetos e empresas autorizados resolvidos pelas tools, não IDs ilustrativos.
Confira também um resultado vazio e um objeto sem fotos/snapshot. Execute os cenários
de `docs/ACCEPTANCE.md` no cliente antes de declarar o aceite visual concluído.

## Fontes oficiais

- [Criar e empacotar skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Usar skills e capacidades de documentos](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- [Instalar plugins no Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)
- [Manifesto de plugins](https://code.claude.com/docs/en/plugins-reference)

A composição é validada localmente. Instalação, OAuth, transporte dos bytes de fotos
e renderização real precisam de conferência em cada cliente.
