# HydroVision Plugin

Consulte dados, analise fotos e produza relatórios com o HydroVision no chat.
Este pacote reúne a skill de análise e a configuração da conexão. As ferramentas
continuam no servidor MCP e respeitam suas permissões no HydroVision.

**A instalação depende do cliente:**

| Cliente | Como instalar este pacote |
|---|---|
| Claude.ai | Enviar `hydrovision-claude.zip` em **Customize → Plugins**. |
| ChatGPT pessoal, desktop com Work/Codex | Instalar pelo catálogo local incluído no repositório. |
| ChatGPT pessoal, navegador | Não há um fluxo equivalente de upload deste ZIP confirmado na documentação consultada. A conexão MCP já cadastrada continua funcionando. |

O pacote não está publicado nos diretórios oficiais. O ZIP do ChatGPT é para instalação
local; enviá-lo como anexo de uma conversa não instala o plugin.

## Obter os arquivos

Se recebeu o ZIP da equipe HydroVision, siga a instalação abaixo. Para gerá-los a partir
deste repositório, use Python 3.10 ou superior, sem instalar dependências:

```bash
python build.py
```

Os arquivos ficam em `dist/hydrovision-claude.zip` e `dist/hydrovision-chatgpt.zip`.
O ZIP automático **Code → Download ZIP** do GitHub contém o projeto inteiro; use os
pacotes gerados acima para instalar.

## Claude.ai

1. Abra **Personalizar / Customize → Plugins → Adicionar / Add → Upload plugin**.
2. Selecione `hydrovision-claude.zip`.
3. Abra o plugin **HydroVision → Connectors**. Se a conexão já estiver ativa, use-a.
   Caso contrário, adicione/conecte o servidor apresentado e faça login no HydroVision.
4. Se o cadastro pedir configuração OAuth, escolha **Use your own OAuth client**:
   Client ID `claude-ai`, Client Secret vazio e escopo `vision:read`, se solicitado.
5. Abra uma conversa e peça uma consulta com o HydroVision.

O plugin inclui a URL do MCP e a skill. O cadastro/autorização do conector ainda é uma
etapa da instalação; o pacote não substitui seu login. Em Team/Enterprise, o responsável
pela organização pode precisar adicionar o conector primeiro. Mantenha sua conexão
HydroVision existente enquanto testa o pacote.

Esses passos seguem a documentação de [instalação de plugins no Claude](https://claude.com/docs/plugins/build)
e [configuração OAuth dos conectores](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp).

## ChatGPT pessoal — desktop

Este pacote usa o aplicativo HydroVision já cadastrado no ChatGPT, identificado em
[.app.json](https://github.com/hydroforce-brasil/HydroVision-Plugin/blob/main/.app.json).
Ele acrescenta a skill à conexão existente. **Mantenha essa conexão:**
ela fornece as ferramentas e o login; o pacote local organiza seu uso.

1. No computador onde usa o ChatGPT desktop, mantenha este repositório ou extraia
   `hydrovision-chatgpt.zip` em uma pasta permanente.
2. Com uma versão do Codex CLI que tenha gerenciamento de plugins, registre essa pasta.
   Exemplo para este checkout; ajuste o caminho se usar outra pasta:

   ```bash
   codex plugin marketplace add ~/work/HydroVision-Plugin
   ```

3. Reinicie o ChatGPT desktop. No modo **Work/Codex**, abra **Plugins**, escolha a origem
   **HydroVision** e instale **HydroVision**.
4. Confirme o acesso ao aplicativo HydroVision solicitado pelo pacote e faça login se necessário.
5. Inicie uma conversa e selecione o plugin HydroVision dessa origem.

Esse é o fluxo de [catálogo local documentado pela OpenAI](https://developers.openai.com/plugins/build/plugins).
Ele depende de suporte a plugins locais na versão instalada. Não pressupõe que a instalação
local aparecerá automaticamente no chat do navegador.

O ID incluído é o da conexão informada pelo mantenedor. **Distribuir o ZIP não compartilha
esse aplicativo com outras contas.** Para outro usuário, a conexão precisa estar disponível
para ele; se cadastrar outro aplicativo, ajuste seu ID em `.app.json`. Compartilhar somente
o pacote não elimina o cadastro manual do MCP para qualquer cliente externo.

### Se usar apenas chatgpt.com

Continue usando o HydroVision que já conectou. O MCP envia suas instruções gerais, mas
isso não instala a skill deste repositório. Para experimentar a orientação nessa conversa,
anexe [SKILL.md](skills/hydrovision-analysis/SKILL.md) e peça:

> Use este guia nas consultas ao HydroVision nesta conversa.

Isso é uma orientação por conversa, não a instalação do plugin. Para distribuir uma
instalação no navegador, há caminhos distintos: importação pelo administrador em um
workspace compatível ou publicação no diretório oficial. O segundo exige preparação e
revisão próprias; este pacote privado, que referencia um aplicativo existente, não é um
ZIP pronto para submissão pública.

### Futuro workspace

Depois de publicar os arquivos no GitHub, o administrador pode usar **Admin → Plugins →
Add → Import marketplace**, com a URL deste repositório e Path vazio. O catálogo referencia
o plugin da raiz. É preciso disponibilizar também o aplicativo de `.app.json` aos usuários;
importar o pacote não concede esse acesso. Consulte a [documentação de distribuição no workspace](https://learn.chatgpt.com/docs/enterprise/plugin-management).

## Cadastro manual da conexão, quando necessário

**Nome:** `HydroVision` · **Autenticação:** `OAuth`

```text
https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp
```

| Campo OAuth | Claude | ChatGPT |
|---|---|---|
| Client ID | `claude-ai` | `chatgpt` |
| Client Secret | Deixe vazio | Deixe vazio |
| Escopo, se solicitado | `vision:read` | `vision:read` |

No ChatGPT, use **Plugins → + → Add custom MCP server**. Em OAuth avançado, escolha
cliente previamente cadastrado, autenticação do cliente `none` e os valores acima.
Confirme com a equipe HydroVision o cadastro da URL exata de callback exibida antes
de conectar. Se a equipe fornecer outro Client ID, use o informado.

- `invalid_client`: confira o identificador e o cadastro no Accounts.
- Erro de redirecionamento: envie à equipe somente o callback, sem parâmetros da tela de login.
- Falha de login: confira a organização selecionada e suas permissões. Sua conta HydroVision
  pode ser diferente da conta Claude/ChatGPT.

## Testar depois de instalar

Primeiro, confira nas ferramentas do cliente que a skill `hydrovision-analysis` está disponível.
Depois, use exemplos como estes, substituindo empresa, logger e período:

- “Use o HydroVision para listar as empresas que posso consultar.”
- “Mostre as fotos de instalação do logger [ID] aqui no chat.”
- “Gere os CSVs de vazamentos de [empresa], em [mês/ano], mostre uma prévia e anexe os arquivos.”
- “Compare as confirmações de vazamentos entre [períodos] e explique a cobertura dos dados.”

Confira o escopo, os totais e os arquivos com o sistema. Exibir imagens, executar cálculos
e criar anexos depende dos recursos do cliente; a skill orienta seu uso, sem garantir uma
capacidade ausente na interface.

## Manutenção

- Edite a skill somente em `skills/hydrovision-analysis/SKILL.md`; os dois ZIPs recebem
  exatamente esse arquivo.
- A identidade e a versão ficam em `.codex-plugin/plugin.json`; `build.py` reaproveita esses
  metadados para gerar o manifesto do Claude. Incremente a versão antes de distribuir uma atualização.
- `build.py` contém a URL pública do MCP. `.app.json` referencia o aplicativo do ChatGPT.
- O empacotamento inclui apenas arquivos explicitamente selecionados, sem `.git`, ambientes,
  credenciais ou dados de clientes. Os ZIPs ficam fora do Git e podem ser distribuídos separadamente.
- Mudanças na skill exigem atualizar/reinstalar o pacote no cliente. As tools e suas instruções
  gerais continuam sendo mantidas e publicadas pelo `simpat-back`.

Este repositório pode ser público: seus identificadores não concedem acesso aos dados.
Não inclua senhas, tokens ou dados de clientes. Publicação nos diretórios oficiais é uma
etapa futura, com requisitos próprios de distribuição, autenticação e revisão:
[Claude](https://claude.com/docs/directory/publish) e
[ChatGPT](https://developers.openai.com/plugins/deploy/submission).
