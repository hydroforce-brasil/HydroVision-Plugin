# HydroVision no Claude e no ChatGPT

Conecte o HydroVision para consultar dados, analisar fotos e gerar relatórios no chat.
As ferramentas são somente leitura e respeitam suas permissões no HydroVision.

## Plugin e coleção de skills

Este repositório gera versões Claude e ChatGPT do plugin `hydrovision`, com quatro skills:

| Skill | Uso |
|---|---|
| `hydrovision-analysis` | Consultas, conceitos, entidades, vazamentos, investigações e comparações. |
| `hydrovision-diagnostics` | Saúde, desempenho, bateria e qualidade/atualização da telemetria. |
| `hydrovision-visualizations` | Gráficos, mapas possíveis, tabelas e imagens integradas ao texto. |
| `hydrovision-reports` | DOCX, PPTX, PDF e XLSX gerenciais/técnicos com identidade institucional. |

O [catálogo de objetos, visões e tools](docs/CATALOG.md) mapeia 33 conceitos,
nove visões e as 28 tools atuais, distinguindo dados disponíveis, parciais e indisponíveis.
As imagens principais aparecem junto aos achados; as demais ficam no apêndice visual
incorporado ao documento ou em galeria no chat. Uma foto não é substituída por um link.

A skill de relatórios incorpora um DOCX e dois PPTX institucionais (claro e escuro).
Os cinco arquivos de origem foram inventariados; apresentações chamadas “Exemplo”
são referências de composição e não entram nos pacotes. Não há dependência de D: no
uso pelo Claude. XLSX deriva da identidade institucional; PDF deriva do editável composto.

Para gerar os arquivos de instalação, com Python 3.10+:

```powershell
python skills/collection.py validate
python -m unittest discover -s skills/tests -v
python skills/collection.py build --output dist/1.1.0
```

O comando produz `dist/1.1.0/claude/hydrovision-plugin.zip` e
`dist/1.1.0/chatgpt/hydrovision-plugin.zip`, além de quatro ZIPs individuais por cliente,
com manifestos e SHA-256. Para gerar só uma versão, use `--target claude` ou `--target chatgpt`.
Use um diretório de saída novo em cada build.
Veja [como instalar](skills/INSTALL.md), [como manter e atualizar](docs/MAINTENANCE.md)
e os [cenários de aceite nos clientes](docs/ACCEPTANCE.md). Conectar o MCP não instala
automaticamente as skills. Cada cliente precisa de instalação e autenticação próprias.

O Claude usa `.claude-plugin/plugin.json` e `.mcp.json`; ChatGPT usa os arquivos
portáteis `plugin.json` e `mcp.json`. A base de skills é neutra, e cada build inclui
seu guia de execução para documentos/imagens e o client ID OAuth correto. No ChatGPT,
há um [guia de instalação e distribuição](docs/INSTALL-CHATGPT.md) e um marketplace local
em `.agents/plugins/marketplace.json`; isso não publica o plugin nem habilita outras contas.

O empacotador e os testes locais usam somente a biblioteca padrão, sem inicializar
Django, consultar bancos ou chamar o MCP. A criação final dos documentos usa as capacidades
disponíveis do cliente; inspeção estrutural local não certifica renderização real.

## Antes de começar

Tenha uma conta ativa no HydroVision com acesso à sua organização e uma conta
Claude/ChatGPT que permita conexões MCP personalizadas. Se a opção não aparecer,
consulte o administrador do workspace.

Se o HydroVision já estiver na lista de conexões, clique em **Conectar** e faça login.

## Dados da conexão

**Nome:** `HydroVision` · **Autenticação:** `OAuth`

**URL do servidor** — copie exatamente:

```text
https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp
```

| Campo OAuth | Claude | ChatGPT |
|---|---|---|
| Client ID | `claude-ai` | `chatgpt` |
| Client Secret | Deixe vazio | Deixe vazio |
| Escopo, se solicitado | `vision:read` | `vision:read` |

Se a equipe HydroVision fornecer outro Client ID para sua conexão, use o informado.

## Claude — claude.ai

1. Abra **Personalizar / Customize → Conectores / Connectors → Adicionar**.
   Escolha **Custom → Web** ou **Adicionar conector personalizado**, conforme a interface.
   Em Team/Enterprise, esse cadastro é feito pelo administrador.
2. Preencha o nome e a URL acima e continue.
3. Selecione **Entrar agora / Sign in now** e **Usar seu próprio cliente OAuth /
   Use your own OAuth client**. Preencha os campos conforme a tabela.
4. Conclua o cadastro. Na tela do HydroVision, selecione sua organização,
   entre com sua conta e autorize a conexão.
5. Abra uma conversa e habilite **HydroVision** no menu **+ → Conectores**.

## ChatGPT — chatgpt.com

1. Abra **Plugins → + → Adicionar servidor MCP personalizado / Add custom MCP server**.
2. Preencha o nome e a URL acima. Selecione **OAuth**.
3. Em **Configurações avançadas de OAuth**, escolha cliente previamente cadastrado
   e use a tabela acima. Se houver método de autenticação do cliente, escolha **Nenhum / none**.
   Mantenha os endpoints detectados automaticamente.
4. Se o ChatGPT exibir uma URL de callback/redirecionamento, envie-a à equipe HydroVision
   para confirmar o cadastro antes de conectar. Uma nova conexão pode ter um callback próprio.
5. Revise o aviso, marque **Entendo e quero continuar** e crie o plugin.
   Conecte, selecione sua organização no HydroVision, faça login e autorize.
6. Instale o plugin, se solicitado. Em uma nova conversa, digite **@HydroVision** e selecione-o.

## Teste a conexão

> Use o HydroVision para listar as empresas e os setores que posso consultar.

## Se não conectar

- **`invalid_client`:** confira o Client ID e peça à equipe HydroVision para verificar o cadastro.
- **Erro de redirecionamento:** peça à equipe para cadastrar o callback exato dessa conexão.
  Envie somente esse endereço; não copie a URL completa da tela de login com seus parâmetros.
- **Falha no login ou acesso negado:** confira a organização escolhida e suas permissões.
  A conta usada para entrar no HydroVision pode ser diferente da conta do Claude/ChatGPT.

Este guia é público. URL e Client IDs não concedem acesso aos dados. Não publique
senhas, tokens ou dados de clientes nas issues.

Documentação oficial: [Claude](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp),
[ChatGPT](https://developers.openai.com/api/docs/guides/custom-mcp-server) e
[OAuth do ChatGPT](https://developers.openai.com/plugins/build/auth).
