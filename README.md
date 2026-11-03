# HydroVision Plugin

Consulte dados, diagnostique loggers, visualize indicadores e produza relatórios
institucionais com o HydroVision dentro do Claude ou do ChatGPT. O plugin reúne quatro
skills (`hydrovision-analysis`, `hydrovision-diagnostics`, `hydrovision-visualizations`,
`hydrovision-reports`), os modelos DOCX/PPTX da Hydroforce e a configuração da conexão MCP.
As ferramentas continuam no servidor MCP e respeitam suas permissões no HydroVision;
o plugin não concede acesso a dados.

Versão atual: veja `skills/collection.json` e [CHANGELOG.md](CHANGELOG.md).

## Instalar

Há dois caminhos. Em ambos a autenticação é OAuth por **CIMD**: o cliente apresenta sua
própria identidade publicada ao Accounts e você só faz login no HydroVision. Não há
Client ID nem Client Secret para colar.

### 1. Marketplace (recomendado no Claude)

| Onde | Como |
|---|---|
| claude.ai / Claude Desktop | **Customize → Plugins → Add marketplace** e informe `hydroforce-brasil/HydroVision-Plugin`; depois instale **HydroVision**. |
| Claude Code | `claude plugin marketplace add hydroforce-brasil/HydroVision-Plugin` e `claude plugin install hydrovision@hydrovision`. |
| ChatGPT (workspace) | O administrador importa o repositório em **Admin → Plugins → Add → Import marketplace** (catálogo `.agents/plugins/marketplace.json`). |
| ChatGPT Desktop / Codex CLI | `codex plugin marketplace add <caminho do clone>` e instale **HydroVision** pela fonte local. |

O marketplace Claude é `.claude-plugin/marketplace.json`, com o plugin na raiz (`./`).
O repositório precisa ser público, ou os membros precisam de acesso ao GitHub para que
o cliente consiga cloná-lo. Atualizações chegam ao reinstalar/atualizar o plugin.

### 2. ZIP pela página **Conectar IA** do HydroVision

Na página **Conectar IA** do HydroVision estão os downloads da versão publicada:
`hydrovision-claude-<versão>.zip` e `hydrovision-chatgpt-<versão>.zip` (este também serve
ao Codex), com SHA-256 e tamanho. Cada clique gera um link temporário; se ele expirar,
clique de novo. São os mesmos arquivos anexados na
[GitHub Release](https://github.com/hydroforce-brasil/HydroVision-Plugin/releases) da tag
correspondente.

- **Claude**: **Customize → Plugins → Add → Upload plugin** com `hydrovision-claude.zip`.
  Se o seu workspace não oferecer upload de plugin, use o marketplace acima.
- **ChatGPT**: `hydrovision-chatgpt.zip` é o pacote portátil (`plugin.json`, `mcp.json`,
  skills, modelos). Extraia-o em uma pasta permanente e registre-a como fonte local
  (`codex plugin marketplace add <pasta>`), ou entregue ao administrador do workspace.
  Enviar o ZIP como anexo de uma conversa não instala o plugin.

Detalhes por cliente: [docs/INSTALL-CLAUDE.md](docs/INSTALL-CLAUDE.md) e
[docs/INSTALL-CHATGPT.md](docs/INSTALL-CHATGPT.md).

## Conexão MCP

| Campo | Valor |
|---|---|
| Servidor | `https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp` |
| Autenticação | OAuth 2.1 com CIMD (sem Client ID/Secret) |
| Escopo | `vision:read` |

Se precisar cadastrar a conexão manualmente, informe somente URL e OAuth; deixe o
cliente descobrir endpoints e identidade. Erros `invalid_client` ou de redirecionamento
indicam que o Accounts não aceitou a identidade/callback do cliente: envie à equipe
HydroVision o cliente usado e o callback exibido, sem tokens ou URLs completas de login.
Sua conta HydroVision pode ser diferente da conta Claude/ChatGPT.

## Testar depois de instalar

Confirme que as quatro skills aparecem no cliente e peça, por exemplo:

- “Use o HydroVision para listar as empresas que posso consultar.”
- “Diagnostique o logger [ID] e mostre as fotos de instalação junto aos achados.”
- “Compare as confirmações de vazamentos entre [períodos] e explique a cobertura.”
- “Gere um relatório técnico em DOCX e PDF com as evidências.”

Os cenários completos estão em [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## Repositório

```text
.claude-plugin/   plugin.json + marketplace.json (Claude)
plugin.json       manifesto portátil (ChatGPT e Codex, agent-plugins + com.openai)
.agents/plugins/  marketplace ChatGPT/Codex
.mcp.json         conexão MCP para Claude      mcp.json  conexão MCP para ChatGPT
skills/           fonte única: SKILL.md, _shared/, _clients/, collection.json, collection.py, tests/
docs/             instalação, manutenção, release, aceite e catálogo gerado
```

- Fonte única das skills: `skills/<nome>/SKILL.md` e `skills/_shared`. O build copia esses
  arquivos; `dist/` e `release/` são saídas locais ignoradas pelo Git.
- Empacotador: `python skills/collection.py build --output dist/<versão>`.
- Versão: `python skills/collection.py bump <x.y.z>` e `check-version`.
- Release: merge em `main` com versão nova → `release.yml` publica no bucket privado,
  cria a tag `v<x.y.z>` e a GitHub Release; o HydroVision entrega o ZIP por URL assinada.

Manutenção: [docs/MAINTENANCE.md](docs/MAINTENANCE.md). Release e contrato com o
HydroVision: [docs/RELEASE.md](docs/RELEASE.md). Catálogo de conceitos e tools:
[docs/CATALOG.md](docs/CATALOG.md).

Este repositório pode ser público: endpoint e identificadores não concedem acesso aos
dados. Não inclua senhas, tokens ou dados de clientes.
