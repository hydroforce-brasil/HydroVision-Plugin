# Modelo conceitual e nomes canônicos

Use rótulos em português nas explicações e códigos do contrato nos argumentos MCP.
O catálogo [concepts.json](concepts.json) descreve relações, campos consultáveis e fontes;
[tools.json](tools.json) mapeia as ferramentas. Conhecer um objeto não o torna consultável.

## Identidade e escopo

Organization → Company é uma projeção; Account → Employee também. UUID do Accounts
não é ID inteiro do Vision. A ligação usa `organization_id`/`account_id` internamente;
esses campos não estão expostos nos datasets atuais. Não tente juntar IDs por igualdade.
`users` consulta Employee, não Account. `company_id` é vínculo; `company_scope_id`,
seleção operacional. Consultas analíticas usam empresas explícitas sem mudar a seleção.

Accounts é dono de organização, identidade, assinatura e concessão. Acesso exige
organização, conta, assinatura do produto e concessão ativas. `ServiceUser` do admin
do Accounts não é Account. Assinaturas/grants e sua vigência não são consultáveis
pelas tools atuais; não diagnostique a autorização completa só pelo dataset `users`.

## Território e ativos

Empresa (Company) → Diretoria (Directory) → Gerência (Management) → Município (City)
→ Localidade (Locale) → Setor (Sector). Setor tem comprimento de rede em metros.
O MCP expõe nomes da hierarquia e filtros, não datasets independentes de todos os níveis.

Ponto de medição = lugar físico; logger = equipamento com MAC. Um ponto pode receber
equipamentos diferentes ao longo do tempo. Relação corrente não reconstrói a instalação
histórica; telemetria guarda também setor/ponto da amostra. Rede de distribuição é
geometria materializada, não distância entre endereços ou pontos GPS.

## Vazamentos, localização e campo

Vazamento é um caso. Seu estado atual vem da última situação registrada por ordem de
cadastro; datas analíticas são primeiras ocorrências. Estados canônicos: `Confirmado`
(confirmado em aberto), `Reparado`, `Pendente` (impedido por terceiro). `Suspeito` é legado
depreciado; sugestão acústica não deve receber esse status como se fosse confirmação.

Uma investigação é uma área poligonal da empresa, sem FK para setor. Possui participantes,
sessões, motivos e evidências. Um vazamento pode não estar vinculado a investigação.
Não infira vínculo por proximidade. Vários participantes/motivos não multiplicam casos.

Cluster de localização pertence a uma execução; seu ID muda a cada execução. Ele não
identifica um lugar permanente e não confirma vazamento. Investigação originada de
sugestão preserva um snapshot; não atualize sua história com o cluster do dia.
Áudio Sense de campo é distinto de AudioData dos loggers.

## Dicionário de indicadores

| Nome canônico | Unidade e interpretação |
|---|---|
| Vazamentos | Casos únicos em `query_data(leaks)`. `leak_summary` conta eventos. |
| Vazão estimada | `estimated_flow_m3_per_day`, m³/dia. Nulo é desconhecido; zero é estimativa zero. |
| Economia projetada | Projeção anual em m³/ano calculada pelo backend. Não é volume medido ou faturamento. |
| Contribuição anual dos reparos do mês | Cada coluna de `dashboard_volume_series` representa m³/ano; não m³ recuperados naquele mês. |
| Tempo até o primeiro reparo | Dias da primeira confirmação ao primeiro reparo elegível; não pareia ciclos de reabertura. |
| Rede varrida | Comprimento de tubulação coberta, em metros/km; não distância caminhada. Somar investigações pode repetir rede. |
| Densidade de achados | Vazamentos por km da rede medida elegível; conferir denominador e medição pendente. |
| Saúde do logger | Combinação dos testes funcionais e qualidade do último dia de transmissão; pode ser desconhecida. |
| Desempenho armazenado | Snapshot com data de cálculo. Severidade não é probabilidade de falha. |
| Dias sem observação | Ausência de dados na janela; sem agenda histórica não é quantidade de coletas perdidas. |
| Utilização para faturamento | Disponibilidade do ponto na regra do endpoint; não assinatura do produto, cobrança ou valor em reais. |

Na dashboard, volume é projeção independente do período; campo usa empresa inteira;
ranking de setores ignora período. Preserve o recorte de cada bloco, mesmo na mesma página.
Comparações exigem unidades, filtros e base temporal equivalentes. Percentual sobre base
zero é indefinido. Não converta nulo em zero nem invente fórmula para substituir métrica.

Datas analíticas: início inclusivo, fim exclusivo, fuso retornado pelo servidor
(atualmente America/Bahia). Respeite formatos REST específicos. Captura, chegada e
cálculo são tempos diferentes. Estado atual não é estado no fim de uma janela histórica.

## Fontes de manutenção

- Backend: `docs/arquitetura/dominio.md`, `web/mcp_server/catalog.py`, `allowlist.py`,
  `queries.py`, `analytics.py`, `web/employee/README.md` e modelos de domínio.
- Accounts: `docs/arquitetura/dominio.md`, `accounts/models.py` e módulo OAuth.
- Frontend: rotas, consumers, presenters e schemas de `report-build`.
- Revisões e hashes são registrados no manifesto de cada pacote. Schemas atuais prevalecem.
