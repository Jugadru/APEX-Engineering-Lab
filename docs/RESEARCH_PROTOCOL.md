# Protocolo científico

1. Questão e hipótese falsificável. Registrar literatura, autoria, URL, data, licença, limitações e aplicabilidade. Distinguir observado, inferido, estimado e medido. Usar IDs Foundation; não importar código sem licença.
2. Definir antes da execução: baseline, candidato, versão Lab, workload, seed, tick, comando, estado inicial, unidades, critérios, número de repetições, orçamento, método de comparação e regras de interrupção. Para A/B: ambiente e dados equivalentes; manter todas as amostras.
3. Registrar plano imutável; executar somente ferramenta revisada/permitida. Não alterar critérios depois de observar resultados. Cada tentativa nova usa ID novo, vinculado à anterior na hipótese/escopo.
4. Salvar métricas brutas, logs, hashes e ambiente. Separar estático, unitário, fixture, simulação, benchmark headless e gráficos nativos. Limites e resultados negativos são conhecimento.
5. Validar envelope e bytes; autenticar proveniência separadamente. PASS/FAIL exigem evidência completa; NOT_RUN não traz observações; BLOCKED/INCONCLUSIVE preservam dados parciais. Nível de maturidade: PROPOSTO, EXPERIMENTAL, VALIDADO_EM_ESCOPO, CANDIDATO_INTEGRACAO, INTEGRADO (somente revisão externa e SHA do alvo). A versão 1 do registro não eleva maturidade automaticamente.
6. Revisão independente quando possível, PR de integração separada, FAST + Test Lab no SHA alvo. Sem publicação automática. Não inferir FPS ou validade em corrida completa de um teste sintético.
