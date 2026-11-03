# Changelog

Todas as mudanças relevantes deste repositório. Formato baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões seguem SemVer.
A versão declarada é única: `python skills/collection.py check-version` confere
`.claude-plugin/plugin.json`, `plugin.json` e `skills/collection.json`.

## [1.2.0] - 2026-11-03

### Adicionado

- Marketplace Claude em `.claude-plugin/marketplace.json`: o repositório pode ser
  adicionado em **Customize → Plugins → Add marketplace** (claude.ai) ou com
  `claude plugin marketplace add hydroforce-brasil/HydroVision-Plugin` (Claude Code).
- Pipeline de release (`.github/workflows/release.yml`): cada push em `main` cuja versão
  ainda não tem tag constrói os dois pacotes, envia `hydrovision-claude.zip`,
  `hydrovision-chatgpt.zip`, `manifest.json` e o ponteiro `latest.json` ao bucket
  **privado** `PLUGIN_RELEASES_BUCKET`, confere o SHA-256 baixado de volta, cria a tag
  `vX.Y.Z` e a GitHub Release. Objetos de versão nunca são sobrescritos.
  O simpat-back lê `latest.json` e entrega o ZIP por URL assinada de curta duração.
- Subcomandos `bump <x.y.z>`, `check-version [tag]` e `stage-release` em
  `skills/collection.py`; o manifesto do build passa a trazer SHA-256 e tamanho de
  cada ZIP de plugin. `latest.json` traz `object` (nome no bucket) e `filename`, sem URLs.
- `validate` recusa arquivos que não são UTF-8 e acentos perdidos (`usu?rios`), defeito
  presente na 1.0.0 instalada, e exige `policy`/`category` no marketplace do Codex.
- `CHANGELOG.md` e `docs/RELEASE.md` (bucket, IAM, segredos, contrato do `latest.json` e
  sugestão de endpoint no simpat-back).

### Alterado

- Autenticação por **CIMD** (Client ID Metadata Document) nos dois clientes: `.mcp.json`
  não fixa mais `oauth.clientId` e `mcp.json` usa `client.mode = "cimd"`. Não há Client ID
  para colar na instalação; o Accounts anuncia `client_id_metadata_document_supported`.
- Versões alinhadas em 1.2.0 em todos os manifestos.
- `skills/hydrovision-analysis/SKILL.md` volta a ser a skill da coleção (descrição com até
  200 caracteres); o texto monolítico antigo já vivia nas referências compartilhadas.
- Documentação reescrita: README, `docs/MAINTENANCE.md`, `docs/INSTALL-CLAUDE.md`,
  `docs/INSTALL-CHATGPT.md`, `docs/ACCEPTANCE.md`.

### Removido

- `.codex-plugin/plugin.json` e `.app.json`: com `extensions.com.openai` no `plugin.json`
  portátil, o ChatGPT/Codex ignora o overlay inteiro; o mapeamento do app registrado nunca
  era aplicado e o pacote ChatGPT/Codex já não os incluía. A conexão vem do `mcp.json`.

- `build.py` legado da raiz; `skills/collection.py build` é o único empacotador.
- Cópias de documentação externa em `tmp/` deixam de ser versionadas (`/tmp/` no `.gitignore`).

## [1.1.0] - 2026-10-26

- Coleção com quatro skills (`analysis`, `diagnostics`, `visualizations`, `reports`),
  referências compartilhadas, modelos institucionais e empacotador `skills/collection.py`.

## [1.0.0] - 2026-10-26

- Primeira skill de análise e pacotes Claude/ChatGPT.

[1.2.0]: https://github.com/hydroforce-brasil/HydroVision-Plugin/releases/tag/v1.2.0
[1.1.0]: https://github.com/hydroforce-brasil/HydroVision-Plugin/compare/602c50b...f076a82
[1.0.0]: https://github.com/hydroforce-brasil/HydroVision-Plugin/commit/602c50b
