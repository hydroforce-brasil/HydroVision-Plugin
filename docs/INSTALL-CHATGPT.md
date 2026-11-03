# Instalar HydroVision no ChatGPT

Use o pacote `hydrovision-chatgpt.zip` publicado na página **Conectar IA** do HydroVision
(ou na GitHub Release), ou a pasta `chatgpt/hydrovision-plugin` de um build local. O ZIP
contém `plugin.json` portátil, `mcp.json`, quatro skills, referências, modelos e scripts.
Não use o ZIP do Claude como se fosse o pacote do ChatGPT.

## Workspace (administrador)

Em **Admin → Plugins → Add → Import marketplace**, informe a URL deste repositório
(catálogo `.agents/plugins/marketplace.json`, fonte `hydrovision-plugins`, plugin na raiz).
A conexão MCP vem do `mcp.json` do próprio pacote (OAuth por CIMD); não há aplicativo
pré-cadastrado para liberar à parte.

## Teste local no ChatGPT Desktop / Codex

Extraia `hydrovision-chatgpt.zip` em uma pasta permanente, ou use um clone do repositório,
e registre a fonte local:

```text
codex plugin marketplace add CAMINHO_ABSOLUTO_DA_PASTA
codex plugin add hydrovision@hydrovision-plugins
```

O ZIP traz `.agents/plugins/marketplace.json` na raiz, apontando para a própria pasta.
No ChatGPT Desktop, depois do primeiro comando, reinicie o aplicativo, abra **Plugins**,
escolha a fonte **HydroVision** e instale.
Enviar o ZIP como anexo de uma conversa não instala o plugin. Para testar somente os
artefatos de um build, use a raiz do build como marketplace: ela tem
`.agents/plugins/marketplace.json` apontando para `./chatgpt/hydrovision-plugin`.

## Conexão MCP e OAuth (CIMD)

O `mcp.json` usa `streamable-http` e declara em `extensions.com.openai.auth`:

| Campo | Valor |
|---|---|
| URL | `https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp` |
| Método | OAuth 2.1 |
| Registro do cliente | `client.mode = "cimd"` (Client ID Metadata Document) |
| Client ID / Secret | Nenhum: o ChatGPT envia a URL do seu documento de metadados como `client_id` |
| Escopo base | `vision:read` |

O Accounts anuncia `client_id_metadata_document_supported` e aceita `none` no token
endpoint, então o ChatGPT se identifica sozinho e você só faz login no HydroVision.
Endpoints vêm de discovery. Não há senha, token, secret ou client ID no pacote; não
adicione um. Se a sua superfície exigir cadastro manual, use **Plugins → + → Adicionar
servidor MCP personalizado**, informe só a URL e OAuth, e deixe o registro do cliente
automático. Em `invalid_client` ou erro de callback, envie à equipe o callback exibido
pela conexão. Conectar somente o servidor não instala as quatro skills.

## ChatGPT Web

Fontes locais não tornam o pacote disponível no ChatGPT Web ou em outras contas. Para
distribuição ampla, use o marketplace importado pelo administrador do workspace ou o
portal oficial de plugins (fluxo **With MCP**), que exige verificação e revisão. Não há
publicação automática no diretório oficial a partir deste repositório.

## Usar e conferir

Selecione o plugin/skill com `@` quando disponível, ou peça “Use o HydroVision...”.
Teste consulta, comparação, diagnóstico com fotos e DOCX/PPTX/PDF/XLSX conforme
`docs/ACCEPTANCE.md`. Imagens devem aparecer no texto e nos documentos; se o executor
não tiver acesso aos bytes, a skill deve declarar a limitação em vez de inventar
anexos ou caminhos `sandbox:`.

Fontes oficiais: [Empacotar plugins](https://developers.openai.com/plugins/build/plugins),
[Autenticação (CIMD)](https://developers.openai.com/plugins/build/auth),
[Skills no ChatGPT](https://learn.chatgpt.com/docs/build-skills),
[Distribuição no workspace](https://learn.chatgpt.com/docs/enterprise/plugin-management).
