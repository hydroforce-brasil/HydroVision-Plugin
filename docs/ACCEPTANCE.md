# Aceite funcional no Claude.ai, Claude Desktop e ChatGPT

Estado inicial: verificações locais executáveis pelo empacotador e testes; conferência
interativa abaixo ainda depende de sessão autenticada em cada cliente. Registre cliente,
versão, data, pacote/hash, cenário, resultado e limitação observada. Não registre tokens.

| Cenário | Comportamento esperado |
|---|---|
| Nome ambíguo | Resolver candidatos e pedir distinção antes de consultar o objeto errado. |
| Instalação por cliente | Manifesto/transporte corretos e quatro skills com referências e modelos completos. |
| OAuth por cliente | CIMD nos dois clientes: sem Client ID/Secret no pacote, escopo `vision:read`, identidade publicada do cliente aceita pelo Accounts e callback válido. |
| Medida ambígua ("qual a média dos vazamentos?") | Uma pergunta curta com opções concretas antes de consultar dados; nenhuma execução de todas as leituras. |
| Pergunta fechada de número ("quantos vazamentos em outubro?") | `get_context` no máximo uma vez e uma agregação; resposta com número, recorte, n e o que foi presumido. |
| Média mensal | Total ÷ meses do período; mês sem ocorrência conta como zero; mês corrente parcial fora ou identificado. |
| Vazão média | Métrica de média do servidor, só sobre casos com estimativa; cobertura informada; nulo não vira zero. |
| Contagem por grupo fora de vazamentos ("loggers por setor") | Uma agregação com `metrics=[count]` e `group_by`, sem percorrer páginas; nome do setor vindo na própria resposta. |
| Estado da frota ("quantos loggers offline?") | `logger_fleet_dashboard`: contagem sobre o total instalado, com percentual; aparelho em estoque fora da conta. |
| Tempo de reparo | Média e mediana do servidor, com n; sem média de médias por setor. |
| Contagem simples fora de vazamentos ("quantas investigações abertas?") | Filtro com `limit=1` e leitura de `page.total`, sem percorrer páginas. |
| Empresa omitida | Usar selecionada e declarar; não ampliar para todas as autorizadas. |
| Outra empresa | Consultas analíticas usam IDs autorizados explícitos; tools REST mantêm seu escopo. |
| Mais de uma página | Continuar com cursor e consulta iguais; total populacional por agregação. |
| Resposta vazia | Distinguir ausência, erro de acesso, tool indisponível e falha de execução. |
| Resultado truncado/limite | Reduzir recorte ou marcar parcial, sem extrapolar. |
| Comparação temporal | Mesma base e unidade; base zero sem percentual; janelas desiguais identificadas. |
| Caso reaberto | Não confundir estado atual com fim do período ou parear ciclos inexistentes. |
| Métricas gerenciais | Economia projetada em m³/ano; campo/volume/ranking com seus próprios recortes. |
| Snapshot ausente/antigo | Resultado desconhecido/desatualizado, sem diagnóstico inventado. |
| Telemetria irregular | Captura, chegada e cálculo separados; dias sem observação não são coletas perdidas. |
| Mapa sem geometrias | Sem tubulação/limites inventados; cluster transitório não vira lugar permanente. |
| Fotos em duas páginas | Usar next_offset; falha parcial não faz repetir/pular a página. |
| Foto visível, bytes indisponíveis | Não fingir incorporação no documento; registrar limitação específica. |
| Fotos no chat | Imagem real junto ao achado, outras em galeria; nenhum link como substituto. |
| DOCX/PPTX | Identidade do modelo preservada; exemplos e placeholders removidos; arquivos editáveis, sem dependência de capacidades de outro cliente. |
| PDF | Layout preservado, figuras renderizadas e legíveis, sem rede. |
| XLSX | Contexto, Indicadores, Dados e Evidências; IDs textuais e imagens incorporadas. |
| CSV mensal | Conteúdo original e hash/tamanho/linhas preservados, seleção mensal explicada. |
| Concordância entre formatos | Mesmos indicadores, unidades, recortes e evidências nos quatro formatos. |

Asserções estruturais locais não substituem estes cenários. Não afirmar que fotos ou
arquivos funcionam em um cliente antes de verificar transporte e renderização nele.
