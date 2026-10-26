# Aceite funcional no Claude.ai, Claude Desktop e ChatGPT

Estado inicial: verificações locais executáveis pelo empacotador e testes; conferência
interativa abaixo ainda depende de sessão autenticada em cada cliente. Registre cliente,
versão, data, pacote/hash, cenário, resultado e limitação observada. Não registre tokens.

| Cenário | Comportamento esperado |
|---|---|
| Nome ambíguo | Resolver candidatos e pedir distinção antes de consultar o objeto errado. |
| Instalação por cliente | Manifesto/transporte corretos e quatro skills com referências e modelos completos. |
| OAuth por cliente | `claude-ai` no Claude; `chatgpt`/`provided`/`none`/`vision:read` no ChatGPT, com callback válido. |
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
