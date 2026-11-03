# Manter, validar, empacotar e publicar

A fonte da coleção é este repositório. `skills/<nome>/SKILL.md` e `skills/_shared`
são a única fonte das skills: o build copia esses arquivos tal como estão, sem gerar
texto. As cópias em `skills/<nome>/references` e o script de relatórios são
materializados por `sync` e versionados para permitir carregar o plugin direto de um
clone (marketplace). `dist/`, `release/` e `tmp/` são locais e ignorados pelo Git.

## Atualizar conteúdo

Edite o `SKILL.md` correspondente (descrição com até 200 caracteres, sem citar o nome
de um cliente), as referências em `skills/_shared`, os scripts canônicos em
`skills/scripts` ou a configuração `skills/collection.json`. Em seguida:

```powershell
python skills/collection.py sync
python skills/collection.py validate
python -m unittest discover -s skills/tests -v
claude plugin validate .
```

O último comando é opcional e valida somente a configuração Claude, exigindo seu CLI.
As configurações ChatGPT portáteis são conferidas pelo empacotador e pelos testes
(CIMD sem `clientId`, sem credenciais, escopo `vision:read`). A descoberta local pode
ser conferida com `codex plugin list --marketplace hydrovision-plugins --available --json`
quando o CLI estiver disponível. Nenhuma dessas verificações certifica autenticação ou
renderização.

`sync` também atualiza `docs/CATALOG.md`. As skills são autossuficientes: referências
relativas não escapam da pasta da skill nem dependem de outra skill instalada.

## Atualizar fontes de domínio

Com `simpat-back`, `hydrovision` e `accounts-back` ao lado deste clone:

```powershell
python skills/collection.py refresh-sources
python skills/collection.py sync
python skills/collection.py validate
```

O refresh lê AST e arquivos para registrar revisões, hashes, tools e campos públicos,
sem importar os apps. Sem os clones, a validação compara com o snapshot em
`skills/_shared/sources.json`, permitindo builds independentes (é o que a CI faz).

## Atualizar modelos

```powershell
python skills/collection.py import-templates "D:\DESIGN\Modelos de Documentos"
python skills/collection.py sync
python skills/collection.py validate
```

Só os três templates configurados como reutilizáveis são copiados para os assets de
relatórios. Revise `branding.md` se modelos mudarem.

## Versão única

A versão vive em três arquivos que devem ser iguais: `.claude-plugin/plugin.json`,
`plugin.json` e `skills/collection.json`. Não recrie `.codex-plugin/` nem `.app.json`:
com `extensions.com.openai` no `plugin.json`, o ChatGPT/Codex ignora o overlay inteiro, e
o `validate` recusa esses arquivos.

```powershell
python skills/collection.py bump 1.3.0        # reescreve os três
python skills/collection.py check-version     # falha se divergirem
python skills/collection.py check-version v1.3.0   # usado pela release: tag == versão
```

Registre a mudança em `CHANGELOG.md`.

## Construir localmente

```powershell
python skills/collection.py build --output dist/1.3.0
```

`build` valida fontes/cópias/modelos e produz `claude/` e `chatgpt/`, cada um com
`hydrovision-plugin.zip`, quatro ZIPs de skill, guia e `manifest.json` com SHA-256.
O `manifest.json` da raiz do build traz, por cliente, o SHA-256 e o tamanho do ZIP do
plugin. O build seleciona arquivos explicitamente: manifesto, configuração MCP, as
quatro skills, `docs/` e o guia de instalação; `dist/`, `tmp/`, `skills/tests`,
`skills/_shared`, `skills/_clients` e `collection.py` nunca entram nos ZIPs.
Datas de ZIP são fixas; fontes idênticas reproduzem os mesmos hashes.

## Publicar uma release

Fluxo: **bump → merge em main → release.yml → bucket privado → simpat-back assina a URL**.

1. `bump`, `check-version`, `validate`, testes e `CHANGELOG.md`; commit, PR e merge em `main`.
2. No push em `main`, `release.yml` vê que a tag `v1.3.0` não existe, valida, testa,
   constrói, executa `stage-release` e envia a `gs://$PLUGIN_RELEASES_BUCKET/hydrovision-plugin/`:
   `1.3.0/hydrovision-claude.zip`, `1.3.0/hydrovision-chatgpt.zip`, `1.3.0/manifest.json`
   e o ponteiro `latest.json` (`Cache-Control: no-cache`). Depois cria a tag `v1.3.0` e a
   GitHub Release com os ZIPs anexados. Push sem bump não publica.
3. O simpat-back lê `latest.json` e devolve ao HydroVision uma URL assinada de curta
   duração para o ZIP escolhido em **Conectar IA**.

Nomes, permissões do bucket, segredo da service account e o contrato do `latest.json`
estão em [RELEASE.md](RELEASE.md). `validate.yml` continua rodando em push/PR sem publicar.

Depois de publicar, execute o aceite interativo em `ACCEPTANCE.md`. A estrutura local não
comprova que o executor do cliente consiga materializar as imagens recebidas pelo MCP.
