# Instalar HydroVision no ChatGPT

Use a pasta/pacote `chatgpt/hydrovision-plugin` do build. O ZIP contém `plugin.json`
portátil, `mcp.json`, quatro skills, referências, modelos e scripts. Não use o ZIP do
Claude como se fosse o pacote de configuração do ChatGPT.

## Teste local no ChatGPT Desktop

O repositório já tem `.agents/plugins/marketplace.json`, com a fonte local
`hydrovision-plugins` apontando para a raiz do plugin. Abra/trabalhe com este repositório
no ChatGPT Desktop e consulte Plugins → fontes locais, reiniciando o aplicativo quando
necessário. Instale HydroVision pela fonte local quando ela estiver disponível nessa
superfície. O marketplace permite descobrir o pacote; não instala nem autentica sozinho.

Para testar somente os artefatos finais, use o diretório raiz do build como marketplace:
ele tem `.agents/plugins/marketplace.json` apontando para `./chatgpt/hydrovision-plugin`.
Não altere caminhos para fora da raiz do marketplace. Não é necessário copiar recursos
manualmente para diretórios internos do aplicativo.

Se já usa Codex CLI, estes comandos são alternativas de configuração local:

```text
codex plugin marketplace add CAMINHO_ABSOLUTO_DO_REPOSITORIO_OU_BUILD
codex plugin list --marketplace hydrovision-plugins --available --json
```

O primeiro registra uma fonte na configuração pessoal; execute apenas se quiser essa
instalação local. O build não executa esse comando. Atualizações de arquivos locais
podem exigir atualizar a fonte/reinstalar e iniciar uma nova conversa.

## Conexão MCP e OAuth

O `mcp.json` usa `streamable-http` e declara autenticação em
`extensions.com.openai.auth` do servidor:

| Campo | Valor |
|---|---|
| URL | `https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp` |
| Método | OAuth |
| Registro | Cliente previamente cadastrado (`provided`) |
| Client ID | `chatgpt` |
| Autenticação no token endpoint | `none`, sem Client Secret |
| Escopo base | `vision:read` |

Os endpoints vêm de discovery. Cadastre o callback exato apresentado pela conexão se
necessário; o pacote não comprova que um callback novo já esteja autorizado no Accounts.
Não troque o client ID por `claude-ai`. Não há senha, token ou secret no pacote.

Se a sua superfície exigir conexão separada, abra **Plugins → + → Adicionar servidor
MCP personalizado**, informe URL/OAuth e cliente previamente cadastrado acima, conforme
as opções disponíveis. Faça login, instale/conecte e inicie uma conversa. Conectar
somente o servidor não instala automaticamente as quatro skills.

## ChatGPT Web e distribuição para outras pessoas

Fontes locais servem para autoria/teste e não tornam o pacote automaticamente disponível
no ChatGPT Web ou em outras contas. Para distribuição, use a fonte privada/gerenciada
suportada pelo seu workspace ou o portal oficial de plugins, fluxo **With MCP**.
Antes do upload, complete o guia `docs/PUBLICATION.md` do pacote, incluindo cadastro,
ícone, casos, conta de demonstração e gravação. O portal recebe o ZIP e usa a
configuração MCP; a publicação exige autenticação, verificação e revisão. Não há publicação automática neste repositório.

Não presuma uma opção genérica de upload de ZIP no chat. No fluxo do portal, o pacote
portátil transporta configurações e recursos; a conexão e os testes continuam necessários.
Os ZIPs individuais são recursos de autoria/importação nas superfícies que os suportam,
não uma garantia de instalação direta no ChatGPT Web.

## Usar e conferir

Selecione o plugin/skill com `@` quando disponível, ou peça “Use o HydroVision...”.
Teste consulta, comparação, diagnóstico com fotos e DOCX/PPTX/PDF/XLSX conforme
`docs/ACCEPTANCE.md`. Criação de documentos usa os recursos realmente disponíveis no
executor; não depende de ferramentas nativas exclusivas do Claude.

Imagens devem aparecer no texto e nos documentos. Ver uma imagem na resposta MCP não
garante acesso aos bytes na ferramenta de código; se faltar esse transporte, a skill
deve declarar a limitação. Arquivos `sandbox:` só são anunciados se realmente existirem
e estiverem acessíveis na sessão. Confira também os documentos sem rede.

Fontes oficiais: [Empacotar plugins](https://developers.openai.com/plugins/build/plugins),
[Skills no ChatGPT](https://learn.chatgpt.com/docs/build-skills),
[Conectar e testar](https://developers.openai.com/plugins/deploy/connect-chatgpt).
