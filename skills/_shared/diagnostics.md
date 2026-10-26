# Diagnóstico orientado por evidências

## Caminhos curtos

| Pedido | Consulta e interpretação |
|---|---|
| Panorama da frota | `logger_fleet_dashboard`; declarar status e escopo considerados. |
| Aparelhos com problemas | `query_data(logger_performance)` com campos mínimos, filtros e paginação; conferir `snapshot_computed_at`. |
| Saúde de um logger | `logger_health`; separar testes do batch mais recente, áudio/pressão do último dia de transmissão e bateria. |
| Queda de bateria | `logger_battery_curve`; preservar unidade/modelo e datas, sem extrapolar vida útil não calculada pela tool. |
| Dado antigo | `data_freshness`; comparar captura, chegada, snapshot e atualização/tentativa de localização. |
| Áudio/pressão ausente ou inválido | `telemetry_quality`, 1–31 dias locais completos; depois detalhe apenas dos casos relevantes. |
| Conferência física | `logger_installation_images`; mostrar as fotos com legenda, separando aparência de desempenho medido. |

## Hipóteses e limites

- Captura recente e chegada atrasada sugerem atraso de transmissão, sem identificar
  sozinhas sua causa. Chegada recente com captura antiga não é medição atual.
- Snapshot antigo e telemetria recente sugerem indicador desatualizado. Data de snapshot
  recente pode representar atualização parcial; não garante todos os cálculos.
- Ausência de snapshot retorna indicadores desconhecidos, não “saudável”.
- Atrasos negativos e valores inválidos precisam ser identificados; não entram nas
  médias elegíveis como se fossem medições normais.
- `logger_performance` combina filtros com AND; a lista REST pode combinar condições
  de áudio/pressão com OR. Valores de sinal armazenados podem diferir da máscara por
  idade da apresentação REST.
- Qualidade de observação não tem agenda histórica confiável: não calcule percentual
  de “coletas perdidas”. O recorte de loggers usa a alocação atual.

Uma recomendação deve apontar logger/ponto, evidência, hipótese e próxima verificação.
Use limites e escores do domínio, sem criar limiares clínicos/operacionais arbitrários
ou confundir alerta acústico com vazamento confirmado. As tools não executam manutenção.
