# Manter, validar e empacotar

A fonte da coleção é este repositório. Não é necessário alterar frontend, backend
ou Accounts para distribuir as skills. `skills/_shared` guarda referências canônicas;
as cópias em cada `skills/<nome>/references` e o script de relatórios são gerados e
versionados para permitir carregar o plugin diretamente de um clone.

## Atualizar conteúdo

Edite o `SKILL.md` correspondente, as referências em `skills/_shared`, os scripts
canônicos em `skills/scripts` ou a configuração `skills/collection.json`. Em seguida:

```powershell
python skills/collection.py sync
python skills/collection.py validate
python -m unittest discover -s skills/tests -v
claude plugin validate .
```

O último comando é opcional e valida somente a configuração Claude, exigindo seu CLI.
As configurações ChatGPT portáteis são conferidas pelo empacotador e pelos testes de
isolamento de OAuth/recursos. A descoberta local pode ser conferida com
`codex plugin list --marketplace hydrovision-plugins --available --json` quando o CLI
estiver disponível. Nenhuma dessas verificações certifica autenticação ou renderização.
Avisos do perfil de submissão ao diretório público
(licença, ícone e política de privacidade) não equivalem a falha de carregamento local;
uma futura publicação precisará resolver esses requisitos sem inventar direitos ou URLs.

`sync` também atualiza o catálogo legível. As skills são autossuficientes: referências
relativas não escapam da pasta da skill nem dependem de outra skill instalada.

## Atualizar fontes de domínio

Com `simpat-back`, `hydrovision` e `accounts-back` ao lado deste clone:

```powershell
python skills/collection.py refresh-sources
python skills/collection.py sync
python skills/collection.py validate
```

O refresh lê AST e arquivos para registrar revisões, hashes, tools e campos públicos,
sem importar os apps. Não altera os três repositórios. Revise diferenças de semântica
nos catálogos: o comando não inventa a documentação de uma tool nova. A validação
compara nomes/fields com o código local quando disponível. Sem os clones, compara com
o snapshot versionado em `skills/_shared/sources.json`, permitindo builds independentes.

Os schemas expostos pela conexão no momento do uso continuam prevalecendo. Um snapshot
de referência não prova que determinada versão esteja implantada no endpoint.

## Atualizar modelos

```powershell
python skills/collection.py import-templates "D:\DESIGN\Modelos de Documentos"
python skills/collection.py sync
python skills/collection.py validate
```

A pasta é somente origem de leitura. O import mantém o hash dos cinco arquivos, temas,
fontes, dimensões e layouts. Só os três templates configurados como reutilizáveis são
copiados para os assets de relatórios; não altera os originais nem empacota os exemplos.
Revise a identidade em `branding.md` se modelos mudarem: cores explícitas podem diferir
das cores herdadas do tema Office. Não há renderer Office embutido no empacotador.

## Construir uma entrega

Atualize a versão em `plugin.json`, `.codex-plugin/plugin.json`,
`.claude-plugin/plugin.json` e `skills/collection.json`
quando distribuir mudança. Use uma pasta nova, por exemplo `dist/1.1.1`, e execute:

```powershell
python skills/collection.py build --output dist/1.1.1
```

`build` valida fontes/cópias/modelos e produz as pastas `claude` e `chatgpt`, cada uma
com plugin, quatro skills independentes, guia e manifesto SHA-256. Use `--target` para
gerar apenas um cliente. O ZIP Claude tem `.claude-plugin`; o ChatGPT tem `plugin.json`
e `mcp.json` portáteis na raiz. Cada ZIP de skill
tem uma única pasta com nome igual ao `name` do SKILL.md. Datas de ZIP são fixas,
permitindo reproduzir hashes com fontes idênticas. Builds existentes não são apagados.
Os artefatos em `dist` são locais e ignorados pelo Git; não há publicação automática.

O teste de empacotamento constrói os dois clientes sem os repositórios vizinhos e
verifica hashes reproduzíveis, raízes de ZIP, referências, modelos idênticos e isolamento
das configurações OAuth. A fonte comum usa linguagem neutra; `skills/_clients` contém
as instruções específicas copiadas como `references/client.md` em cada pacote.
Os testes de documento usam fixtures sintéticas para detectar imagem externa, mídia
órfã/ausente, legenda ausente, contexto inválido e corrupção dos CSVs originais.

Depois do build, execute o aceite interativo em `ACCEPTANCE.md`. A estrutura local não
comprova que o executor do Claude consiga materializar as imagens recebidas pelo MCP.

O comando `python build.py --output-dir dist/NOVA-VERSAO` usa esse mesmo empacotador
e acrescenta os nomes de ZIP históricos na raiz da entrega. Mantenha a apresentação
do manifesto de compatibilidade sincronizada com o portátil. Para o diretório público,
complete [PUBLICATION.md](PUBLICATION.md); o ZIP técnico ainda não é uma submissão pronta.
