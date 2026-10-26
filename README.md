# HydroVision Plugin

Consulte dados autorizados, investigue loggers e produza análises e relatórios do
HydroVision no ChatGPT. O plugin reúne quatro skills, referências de domínio,
modelos institucionais e a conexão com o servidor MCP existente. O acesso ao sistema
usa OAuth e as permissões da conta HydroVision de cada pessoa.

**Estado: pacote de desenvolvimento; ainda não publicado no diretório do ChatGPT.**
O build local não certifica autenticação de outros usuários nem aprovação pública.
As pendências estão em [Preparar a publicação](docs/PUBLICATION.md).

## O que está incluído

| Skill | Uso |
|---|---|
| `hydrovision-analysis` | Consultas, comparações de períodos, vazamentos e exportações CSV. |
| `hydrovision-diagnostics` | Saúde, bateria, desempenho e qualidade dos dados dos loggers. |
| `hydrovision-visualizations` | Gráficos, mapas e tabelas com escopo, unidades e cobertura. |
| `hydrovision-reports` | Relatórios com três modelos institucionais DOCX/PPTX, referências e validação de evidências. |

As ferramentas do MCP são somente leitura. A geração de DOCX, PDF, PPTX ou XLSX
usa os recursos do cliente; o pacote não instala um executor Office nem garante
que toda superfície consiga produzir ou renderizar esses formatos.

## Gerar o pacote completo

Use Python 3.10 ou superior, sem dependências adicionais:

```bash
python build.py --output-dir dist/1.1.1
```

O comando delega ao empacotador da coleção e mantém os nomes antigos de ZIP:

| Arquivo | Conteúdo |
|---|---|
| `dist/1.1.1/hydrovision-chatgpt.zip` | `plugin.json`, `mcp.json`, quatro skills, referências, scripts e modelos. |
| `dist/1.1.1/hydrovision-claude.zip` | A mesma coleção, com configuração própria do Claude. |
| `dist/1.1.1/chatgpt/hydrovision-plugin.zip` | Cópia idêntica do ZIP ChatGPT. |
| `dist/1.1.1/manifest.json` | Inventário da entrega; os manifestos de cada cliente contêm hashes SHA-256. |

Para gerar apenas ChatGPT, acrescente `--target chatgpt`. Use uma pasta nova para
cada build: entregas existentes não são sobrescritas. O comando canônico também
continua disponível:

```bash
python skills/collection.py build --output dist/release --target chatgpt
```

O ZIP de **Code → Download ZIP** do GitHub contém o repositório, não é o pacote
final. Anexar um ZIP a uma conversa não instala um plugin.

## Instalar e compartilhar

| Objetivo | Caminho |
|---|---|
| Testar localmente no desktop/Codex compatível | Registrar o marketplace do repositório ou do diretório de build e instalar HydroVision. |
| Testar a conexão no ChatGPT | Adicionar o MCP remoto por uma superfície que suporte essa criação e autenticar no HydroVision. Isso, isoladamente, não instala as skills. |
| Disponibilizar a um workspace | Importação/publicação gerenciada com as permissões do administrador. Essa disponibilidade fica dentro do workspace. |
| Distribuir pelo diretório a outras contas pessoais | Preparar o pacote, materiais e conta de demonstração; passar por revisão e publicar no diretório universal. |

Consulte [Instalação ChatGPT](docs/INSTALL-CHATGPT.md) e
[Instalação Claude](docs/INSTALL-CLAUDE.md). A fonte local chama-se
`hydrovision-plugins`; a disponibilidade depende da versão e da superfície.
O compartilhamento no workspace não torna o plugin acessível a contas pessoais
externas. Um repositório público também não concede acesso aos dados do HydroVision.

## Conexão MCP

```text
https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp
```

| Configuração ChatGPT | Valor |
|---|---|
| Transporte | Streamable HTTP |
| Autenticação | OAuth |
| Registro de cliente | `provided` |
| Client ID | `chatgpt` |
| Autenticação no token endpoint | `none` — sem Client Secret |
| Escopo | `vision:read` |

O `mcp.json` preserva essa configuração. Endpoints OAuth vêm do discovery;
o callback exato de cada conexão precisa estar registrado no servidor de contas.
O Client ID é um identificador público, não uma credencial de acesso.
Cada pessoa deve autenticar sua própria conta HydroVision e receber apenas os dados
que o backend autoriza. Confirme isolamento entre empresas, expiração e revogação
antes de liberar a terceiros; instruções em skills não substituem autorização no servidor.

A `.app.json` e o manifesto de compatibilidade `.codex-plugin/plugin.json` preservam
a integração privada anterior para clientes que ainda a usam. O build portátil de
ChatGPT exclui esses vínculos de aplicativo e usa o MCP remoto. Não distribua o
repositório inteiro como ZIP de submissão pública.

## Conferir e manter

```bash
python skills/collection.py validate
python -m unittest discover -s skills/tests -v
```

Os testes verificam empacotamento, integridade dos modelos, referências, isolamento
de OAuth e validação de evidências. O aceite com login, fotos e documentos no cliente
está em [ACCEPTANCE.md](docs/ACCEPTANCE.md). Os casos de revisão pública em
`plugin.json` são rascunhos e precisam de conta de demonstração e execução.

Use [MAINTENANCE.md](docs/MAINTENANCE.md) para atualizar fontes, versões e modelos.
O servidor e as regras de acesso continuam sob responsabilidade dos projetos
HydroVision/Accounts existentes. Não inclua tokens, senhas ou dados de clientes no pacote.

Fontes oficiais consultadas em 26/10/2026:
[empacotamento](https://developers.openai.com/plugins/build/plugins),
[autenticação](https://developers.openai.com/plugins/build/auth) e
[submissão e publicação](https://developers.openai.com/plugins/deploy/submission).
