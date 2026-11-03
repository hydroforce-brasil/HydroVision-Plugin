# Instalar HydroVision no Claude

Duas formas, com o mesmo conteúdo (`.claude-plugin/plugin.json`, `.mcp.json` e quatro
skills com referências e modelos):

## Pelo marketplace

- **claude.ai / Claude Desktop**: **Personalizar / Customize → Plugins → Add marketplace**,
  informe `hydroforce-brasil/HydroVision-Plugin` e instale **HydroVision**.
- **Claude Code**: `claude plugin marketplace add hydroforce-brasil/HydroVision-Plugin`
  e depois `claude plugin install hydrovision@hydrovision`.

O repositório precisa ser público ou os membros precisam de acesso ao GitHub. O
marketplace é `.claude-plugin/marketplace.json`; o plugin é a raiz do repositório.

## Pelo ZIP

Baixe `hydrovision-claude.zip` na página **Conectar IA** do HydroVision (ou na GitHub
Release da versão) e use **Customize → Plugins → Adicionar / Add → Upload plugin**.
Confira o SHA-256 exibido na página se quiser validar o download.
No Claude Code, extraia o ZIP numa pasta permanente e rode
`claude plugin marketplace add <pasta>` e `claude plugin install hydrovision@hydrovision`:
o ZIP traz `.claude-plugin/marketplace.json` apontando para a própria raiz.
Se o seu workspace não oferecer upload de plugin, use o marketplace acima ou envie os
quatro ZIPs individuais de skill em **Customize → Skills → Upload a skill** e conecte o
MCP separadamente. Não instale ZIPs individuais e o plugin ao mesmo tempo.

Habilite criação e edição de arquivos/execução de código e as capacidades de documentos
disponíveis no cliente; a coleção não as instala automaticamente.

## Conexão e login

| Conexão | Valor |
|---|---|
| Servidor | `https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp` |
| Autenticação | OAuth 2.1 com CIMD |
| Client ID / Secret | Nenhum: o Claude apresenta sua identidade publicada |
| Escopo | `vision:read` |

Abra o plugin **HydroVision → Connectors** e faça login no HydroVision com a organização
desejada. Se o cadastro pedir configuração OAuth, mantenha a opção padrão do Claude; não
escolha "Use your own OAuth client" nem informe um Client ID. Em `invalid_client` ou erro
de redirecionamento, envie à equipe o callback exibido, sem tokens, URLs completas de
login ou senhas. Não reutilize credenciais ou configuração do ChatGPT.

Comece com “Use o HydroVision para listar as empresas que posso consultar”. Depois
teste diagnóstico com fotos e um relatório com imagens no corpo/apêndice visual.
Modelos já estão incorporados; não é necessário acesso a D: pelo executor.

Instalação, OAuth e renderização real precisam ser conferidos nesta superfície. O
validador estrutural não prova que o executor consiga materializar as fotos do MCP.

Fontes: [Skills no Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude),
[Plugins no Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude),
[Marketplaces de plugins (Claude Code)](https://code.claude.com/docs/en/plugin-marketplaces).
