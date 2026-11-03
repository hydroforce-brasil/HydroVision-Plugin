# Release: bucket privado, CI e contrato com o HydroVision

Os pacotes instaláveis não ficam no Git. Cada push em `main` roda
`.github/workflows/release.yml`: se a versão declarada ainda não tem a tag `v<versão>`, o
workflow valida, constrói os dois pacotes, envia ao bucket **privado** do Google Cloud
Storage, cria a tag e a GitHub Release. Se a tag já existe, ele só registra um aviso.
`validate.yml` valida todo push/PR e não publica nada.

O download chega ao usuário pelo HydroVision: o simpat-back lê o ponteiro `latest.json`
com a própria service account e devolve uma **URL assinada (V4) de curta duração** para o
ZIP pedido. Nenhum objeto do bucket é público.

## Nomes fixos

| Item | Valor | Onde |
|---|---|---|
| Projeto GCP | `simpat-365923` | o mesmo do simpat-back |
| Bucket | `hydrovision-plugin-releases` (privado, `us-central1`) | variável de repositório `PLUGIN_RELEASES_BUCKET` |
| SA do CI | `hydrovision-plugin-ci@simpat-365923.iam.gserviceaccount.com`, `roles/storage.objectUser` só no bucket | segredo `GCP_PLUGIN_RELEASES_SA_KEY` |
| SA do simpat-back | `625238906243-compute@developer.gserviceaccount.com` (a do `GCS_SA_KEY`, segredo `gcp_user_key`, e também a de execução do Cloud Run), `roles/storage.objectViewer` só no bucket | já configurada no backend |
| Prefixo | `hydrovision-plugin/` | `RELEASE_PREFIX` em `skills/collection.py` |

Layout dos objetos:

```text
hydrovision-plugin/<versão>/hydrovision-claude.zip
hydrovision-plugin/<versão>/hydrovision-chatgpt.zip     # ChatGPT e Codex
hydrovision-plugin/<versão>/manifest.json               # manifesto do build (SHA-256, tamanhos, origem)
hydrovision-plugin/latest.json                          # ponteiro; único objeto sobrescrito
```

Os objetos de uma versão sobem com `--no-clobber` e nunca são sobrescritos. O CI baixa os
ZIPs de volta e confere o SHA-256 antes de trocar o `latest.json`, que sobe com
`Cache-Control: no-cache`.

## 1. Criar o bucket e as permissões (uma vez)

Não há `gcloud` nesta máquina: use o **Cloud Shell** (ícone `>_` no topo do Console GCP,
já autenticado) ou qualquer máquina com o Google Cloud CLI. Quem executa precisa de
`Storage Admin` e `Service Account Admin` no projeto.

```bash
PROJECT=simpat-365923
BUCKET=hydrovision-plugin-releases
gcloud config set project "$PROJECT"

# Bucket privado: acesso uniforme e prevenção de acesso público forçada.
gcloud storage buckets create "gs://$BUCKET" \
  --location=us-central1 --default-storage-class=STANDARD \
  --uniform-bucket-level-access --public-access-prevention

# Service account usada só pelo GitHub Actions para publicar.
gcloud iam service-accounts create hydrovision-plugin-ci \
  --display-name="HydroVision plugin releases (GitHub Actions)"
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:hydrovision-plugin-ci@$PROJECT.iam.gserviceaccount.com" \
  --role=roles/storage.objectUser
gcloud iam service-accounts keys create plugin-ci-key.json \
  --iam-account="hydrovision-plugin-ci@$PROJECT.iam.gserviceaccount.com"

# Leitura para o simpat-back. Use o client_email do JSON em GCS_SA_KEY (a SA que já assina
# as URLs de fotos). Se o backend roda sem GCS_SA_KEY, é a SA do serviço Cloud Run.
BACKEND_SA=COLE_AQUI_O_CLIENT_EMAIL
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member="serviceAccount:$BACKEND_SA" --role=roles/storage.objectViewer
```

Pelo Console, o equivalente é: **Cloud Storage → Buckets → Create**, nome
`hydrovision-plugin-releases`, região `us-central1`, classe Standard, controle de acesso
**Uniform**, marcar **Enforce public access prevention**; depois **Permissions → Grant
access** no bucket para as duas service accounts com os papéis acima. Não conceda papéis
no projeto, só no bucket.

## 2. Configurar o GitHub (uma vez)

Em `hydroforce-brasil/HydroVision-Plugin` → **Settings → Secrets and variables → Actions**:

- **Variables** → `PLUGIN_RELEASES_BUCKET` = `hydrovision-plugin-releases` (só o nome, sem `gs://`).
- **Secrets** → `GCP_PLUGIN_RELEASES_SA_KEY` = conteúdo inteiro de `plugin-ci-key.json`.

Apague `plugin-ci-key.json` em seguida (`rm plugin-ci-key.json` no Cloud Shell).
Sem a variável ou o segredo, o job `release` falha logo no início com a mensagem de
configuração; nada é enviado.

## 3. Publicar uma versão

```powershell
python skills/collection.py bump 1.2.1
python skills/collection.py validate
python -m unittest discover -s skills/tests -v
# atualizar CHANGELOG.md, commitar, abrir PR e mesclar em main
```

O merge em `main` publica `1.2.1`. Um push em `main` sem novo `bump` não publica. Para
reproduzir localmente o que vai para o bucket:

```powershell
python skills/collection.py build --output dist/1.2.1
python skills/collection.py stage-release --build dist/1.2.1 --output release
```

A pasta `release/` fica com a mesma árvore do bucket. `release/` e `dist/` são ignorados
pelo Git. Para rodar de novo uma publicação que falhou no meio, use **Run workflow** em
Actions (`workflow_dispatch`): os objetos já enviados são mantidos e só os que faltam sobem.

## Contrato do `latest.json`

Gerado por `stage-release`. Chaves exatas, nesta ordem:

```json
{
  "version": "1.2.0",
  "published_at": "2026-11-03T16:22:12Z",
  "packages": {
    "claude": {
      "object": "hydrovision-plugin/1.2.0/hydrovision-claude.zip",
      "filename": "hydrovision-claude-1.2.0.zip",
      "sha256": "<hex>",
      "size_bytes": 13854577
    },
    "chatgpt": {
      "object": "hydrovision-plugin/1.2.0/hydrovision-chatgpt.zip",
      "filename": "hydrovision-chatgpt-1.2.0.zip",
      "sha256": "<hex>",
      "size_bytes": 13857608
    }
  }
}
```

- `version`: igual à tag sem `v` e à versão de `.claude-plugin/plugin.json`, `plugin.json`
  e `skills/collection.json`.
- `published_at`: UTC, `YYYY-MM-DDTHH:MM:SSZ`.
- `packages.<cliente>.object`: nome do objeto no bucket, para assinar. Não é URL.
- `packages.<cliente>.filename`: nome sugerido para o download (`Content-Disposition`).
- `packages.<cliente>.sha256` / `size_bytes`: do ZIP publicado, iguais ao `manifest.json` do build.
- Clientes: `claude` (Claude: claude.ai, Desktop, Code) e `chatgpt` (ChatGPT e Codex).

## Endpoint no simpat-back (para a equipe de backend)

Sugestão de contrato. O backend já tem `util.storage_utils.generate_signed_url(blob_name,
expires_in_seconds, bucket_name, as_attachment)` com a SA de `GCS_SA_KEY`; basta apontar
para o bucket novo.

- Setting `AI_PLUGIN_BUCKET` (padrão `""` = recurso desligado) e, se quiser, o prefixo fixo
  `hydrovision-plugin`.
- `GET /ai-plugin/` (autenticado): lê `gs://<bucket>/hydrovision-plugin/latest.json` com o
  cliente de storage (cache em memória de ~5 min) e devolve
  `{version, published_at, packages: {claude: {sha256, size_bytes}, chatgpt: {...}}}`, sem URLs.
  Bucket vazio ou ilegível → `ai_plugin: null`/404, nunca 500.
- `GET /ai-plugin/<client>/download/` (autenticado, `client` ∈ `claude|chatgpt`; outro → 404):
  assina `packages[client].object` com expiração curta (5–15 min), `as_attachment=True` e o
  `filename` do ponteiro, e responde `{url, expires_at, version, sha256, size_bytes}` (ou
  `302` para a URL). Gere a URL a cada clique; não guarde nem envie ao log.
- Não aceite `object`, versão ou bucket vindos do request: sempre do `latest.json`.
- No front, o botão chama o endpoint de download e só então abre a URL; a URL expira, por
  isso não deve ser renderizada no carregamento da página.

## Actions de terceiros fixadas por SHA

Em `release.yml`, `google-github-actions/auth` e `google-github-actions/setup-gcloud`
recebem a chave da SA, por isso são referenciadas pelo SHA completo do commit, com a tag
como comentário. Para atualizar, resolva a nova tag
(`git ls-remote https://github.com/google-github-actions/auth refs/tags/vX.Y.Z`) e troque
SHA e comentário juntos. A GitHub Release é criada com o `gh` do runner e o `GITHUB_TOKEN`.

Alternativa sem chave de longa duração: Workload Identity Federation (`permissions:
id-token: write` no job e `workload_identity_provider` + `service_account` no
`google-github-actions/auth`). Exige criar o pool/provider no projeto.

## Reverter

Publique uma versão nova (por exemplo `1.2.2`) em vez de apagar objetos. Se for
imprescindível voltar o ponteiro, gere o `latest.json` de um build anterior com
`stage-release` e envie só esse objeto:
`gcloud storage cp --cache-control=no-cache release/hydrovision-plugin/latest.json gs://hydrovision-plugin-releases/hydrovision-plugin/latest.json`.
