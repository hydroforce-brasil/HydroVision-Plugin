# Preparar a distribuição pública do HydroVision

Estado em 26/10/2026: pacote de desenvolvimento 1.1.1, ainda incompleto para
submissão pública. Nenhum upload, envio à revisão ou publicação foi realizado.
O objetivo é disponibilizar a integração a pessoas em suas próprias contas ChatGPT,
cada uma autenticada no HydroVision com suas permissões.

## Base técnica preparada

- MCP remoto existente em HTTPS, Streamable HTTP, OAuth `provided`, cliente `chatgpt`,
  autenticação do cliente `none` e escopo `vision:read`.
- Quatro skills com referências, scripts e os três modelos institucionais existentes.
- Build completo via `build.py` ou `skills/collection.py`; vínculo privado `.app.json`
  preservado no repositório e excluído do ZIP portátil ChatGPT.
- Identidade/versionamento sincronizados; subtítulo de 29 caracteres e categoria
  `Data & Analytics`.
- Cinco casos positivos, três negativos e prompts escritos em
  `plugin.json → extensions.com.openai.review`; release notes em `publication`.

O nome Hydroforce foi preservado dos metadados existentes. Isso não comprova que
seja a identidade jurídica/verificada que será usada para publicação.

## 1. Confirmar a apresentação pública

Proposta atual para correção pelo mantenedor:

- Nome: **HydroVision**.
- Subtítulo: **Análises de água e vazamentos**.
- Público: pessoas com conta HydroVision autorizada que precisam consultar vazamentos,
  diagnosticar loggers e preparar relatórios.
- Descrição base: consta no manifesto; ainda precisa da revisão editorial do mantenedor
  e da versão em inglês exigida como base pelo fluxo de publicação. Textos em português
  poderão ser fornecidos em `publication.translations`.

Confirmar antes de preencher os campos restantes:

1. Identidade individual ou empresarial verificada que publicará o plugin.
2. Países atendidos: códigos específicos ou decisão explícita por todos os disponíveis.
3. Se o plugin envolve pagamentos/compras; se houver, o que é comprado e onde.
   Não inferir isso da existência de um sistema comercial.

Obter e verificar estas quatro páginas públicas HTTPS, preenchendo os campos em
`extensions.com.openai.interface` somente após confirmar seu conteúdo:

| Campo | Conteúdo necessário | Estado |
|---|---|---|
| `websiteURL` | Página que identifique HydroVision, finalidade e publicador. | Não informado/verificado. |
| `supportURL` | Página com canal funcional de suporte. | Não informado/verificado. |
| `privacyPolicyURL` | Política publicada que cubra os dados e práticas reais desta integração. | Não informado/verificado. |
| `termsOfServiceURL` | Termos publicados aplicáveis ao plugin. | Não informado/verificado. |

Para preparar política/termos, confirmar coleta, uso, compartilhamento, retenção,
exclusão, atendimento e condições de acesso reais. Não preencher URLs presumidas nem
prometer práticas ainda não confirmadas. O link do repositório não substitui esses campos.

O pacote ainda precisa do ícone oficial em PNG quadrado: logo com pelo menos 256×256
e ícone do composer com pelo menos 48×48, até 5 MiB cada. Reutilizar a identidade
HydroVision fornecida pelo mantenedor; referenciar arquivos reais por `logo` e
`composerIcon`. A cor existente `#00539C` foi preservada. Variantes escuras são opcionais.

## 2. Preparar demonstração e testes

Usar uma conta dedicada com dados sintéticos. Não colocar credenciais, identificadores
de clientes reais ou resultados de produção no GitHub ou no ZIP. Os dados da conta
atual não são evidência apropriada para uma revisão pública.

Preparar uma empresa selecionada com vazamentos de agosto/setembro de 2026 e um
logger único chamado **Demo-01**, com fotos de instalação e dados de saúde. Esses são
requisitos de fixture propostos, não registros já criados. Confirmar nomes/períodos
e atualizar os casos se a equipe preferir outro conjunto.

| Caso no manifesto | Cobertura | Estado |
|---|---|---|
| P1 | Empresas autorizadas e paginação. | Not run na conta de demonstração. |
| P2 | Comparação de confirmações entre períodos equivalentes. | Not run. |
| P3 | CSVs completos, prévia e integridade. | Not run. |
| P4 | Resolução de logger, saúde e fotos. | Blocked: fixture ainda não verificada. |
| P5 | Relatório DOCX/PDF com agregação e gráfico incorporado. | Blocked: fixture e executor de demonstração não verificados. |
| N1 | Não executar alteração de vazamento. | Not run. |
| N2 | Não executar reinício/configuração de dispositivo. | Not run. |
| N3 | Não atribuir previsão meteorológica ao HydroVision. | Not run. |

Um teste de conectividade separado na conexão já disponível respondeu a
`get_context(limit=1)` e `describe_data(dataset=leaks)` em 26/10/2026. Ele confirma
respostas autenticadas e descoberta de schema nessa sessão, sem certificar instalação
deste pacote, isolamento entre contas, login novo ou os oito casos acima. Não foram
incluídos os dados retornados nesse teste.

Verificar também no código/scan do servidor que cada tool tem `readOnlyHint`,
`openWorldHint` e `destructiveHint` booleanos coerentes. As descrições disponíveis
nesta inspeção não expuseram essas anotações; elas permanecem não verificadas.
O código do servidor não está neste repositório.

Roteiro para gravar na versão preparada, após instalar/conectar no cliente pretendido:

1. Mostrar HydroVision instalado, versão 1.1.1 e conta de demonstração conectada.
2. Executar o prompt P1 e mostrar a seleção/limitação de escopo.
3. Executar P2 e conferir totais, período e cobertura com as respostas reais.
4. Executar P3, abrir a prévia e um arquivo CSV gerado.
5. Executar P4 e mostrar fotos com legenda e diagnóstico baseado em evidências.
6. Executar P5, abrir o DOCX/PDF e conferir gráfico, fontes e layout.
7. Executar N1, N2 e N3 e mostrar os limites sem alegar ações executadas.

Ensaiar antes; gravar resultados reais com o gravador de tela disponível, mantendo
senhas/tokens fora da captura. Conferir legibilidade e reprodução do vídeo final.
Hospedar no destino escolhido pelo mantenedor, acessível aos revisores, e verificar
reprodução sem login privado. Só então preencher `review.demo_recording_url` e
reconstruir o ZIP. Este roteiro não é um vídeo e não completa a exigência de gravação.

A conta de revisão deve poder entrar e executar todos os casos sem depender do email,
telefone ou conta pessoal do criador. Informar credenciais e instruções somente nos
campos seguros do portal. Registrar o resultado real de cada caso (Passed, Failed,
Blocked ou Not run), sem inventar totais ou adicionar campos de resultado ao manifesto.

## 3. Concluir pacote e configuração no portal

Depois de completar a apresentação e a demonstração:

1. Construir em pasta nova e inspecionar o ZIP: manifesto, `mcp.json`, quatro skills,
   recursos, ícones, casos e metadados. O upload público não deve conter `.app.json`
   ou declarações `apps`. Preservar vínculos gerados pelo portal na versão salva.
2. Quando solicitado pelo mantenedor, enviar o ZIP como rascunho no portal, usando
   a organização e identidade corretas. Upload não equivale a envio para revisão.
3. Completar verificação do desenvolvedor e do domínio MCP. O endpoint atual está
   em Cloud Run; verificar se é possível servir o desafio no host exigido. Um domínio
   próprio pode facilitar operação e identidade, mas não deve ser inventado nem
   substituir o endpoint sem configurar e testar o servidor.
4. Registrar o callback exato apresentado pelo fluxo no Accounts e conectar via OAuth.
   Testar login com uma segunda conta sem permissões administrativas, escopo entre
   empresas, token expirado e acesso revogado. Skills não são controle de autorização.
5. Conferir os campos importados e resolver scans de metadados, skills e tools.
   Completar atestações legais/políticas com o desenvolvedor autorizado.
6. Enviar para revisão quando autorizado. Após aprovação, publicar quando autorizado.
   Não prometer prazo ou aprovação.

Após publicar, cada pessoa deverá instalar o plugin e autorizar a própria conta
HydroVision. Disponibilidade e funcionalidades dependem da conta e da superfície
ChatGPT; não presumir instalação por simples envio de ZIP ou por link privado de
workspace para contas externas.

## Referências oficiais

- [Empacotamento e distribuição](https://developers.openai.com/plugins/build/plugins)
- [OAuth e validação de tokens](https://developers.openai.com/plugins/build/auth)
- [Preparação, revisão e publicação](https://developers.openai.com/plugins/deploy/submission)

Essas referências foram consultadas em 26/10/2026. Revalidar requisitos no momento
da submissão; a validação offline do projeto não substitui as verificações do portal.
