# Strategy Research Lab

**Estado:** 0.9.6 homologada (PR #64 e main eaa6c10: 10/10 cada); 0.9.7 candidata.

## Mandato

Monte Carlo, VSE, undercut/overcut, previsão imperfeita, pit windows, double stack e stints.

## Restrições

Comparar heurística simples antes de ML; informação disponível no tick; sem vazamento do futuro.

## Entrega e aceitação

Comparação de estratégias com seeds e incerteza. Toda entrega exige hipótese, critérios prévios, revisão exata, evidência e limitações. Consulte [protocolo](../../docs/RESEARCH_PROTOCOL.md). Não assumir integração automática.

## Primeira capacidade

`strategy_weather_decision`: 32 episódios sintéticos de oito voltas, um pit obrigatório antes de uma volta, dois pneus artificiais, clima binário observado, 32 previsões por decisão. Heurística troca por incompatibilidade ou metade do horizonte; Monte Carlo replaneja com previsão estocástica e informação atual. Os caminhos de previsão são comuns às alternativas e a geração dos episódios de teste usa seed separada. Oráculo retrospectivo somente para avaliação. Critérios pré-declarados: zero ações inválidas, divergências de replay ou regret negativo. Diferença de regret é exploratória, não critério de aprovação. Não é VSE, não simula tráfego, double stack ou pneus reais. Nenhuma integração esportiva autorizada.

## Auditoria da primeira candidata

A avaliação original observou regret médio de 5725 ms para a heurística e 8850 ms para Monte Carlo (32 casos). A política amostrada otimiza um plano fixo e replaneja depois; não é uma solução ótima de controle adaptativo. Não selecionar seeds/limiares depois de observar os casos; preservar esse resultado e desenvolver referência adaptativa causal em experimento posterior. A auditoria corrige entradas fracionárias/booleanas de pit, valida estado inicial antes da troca, verifica custo total contra o plano realmente aplicado e testa todas as 16 sequências binárias de quatro voltas para três regimes e ambas as políticas.

## Referência adaptativa 0.9.1

Modelo de decisão causal: estado (voltas restantes, pneu, idade, clima atual, pit já feito), ações aguardar ou trocar para seco/molhado. Bellman minimiza custo esperado em milissegundos, com numerador inteiro e denominador 1000^(voltas restantes−1). Probabilidade de transição conhecida, risco neutro. Um pit obrigatório; nenhum acesso ao clima futuro real. Empate determinístico: seco, molhado, aguardar. Comparação exata ponderada das 256 sequências binárias de oito voltas em cada regime 0/250/500/1000 por mil; pesos de clima inicial iguais. O replay verifica valor esperado, causalidade, custo e legalidade contra as políticas originais. Amostra separada de 64 casos com seed 20261127 e forecast seed 42; resultado amostral exploratório. Não alterar critérios após observação; não confundir ótimo deste modelo sintético com ótimo real. REF-106/IDEA-041/045/048 são referências conceituais do portfólio, nenhum código externo copiado.

## Weather Prediction Intelligence 0.9.2

O clima atual é observado, mas a taxa de mudança é desconhecida. Dois regimes sintéticos de 100 e 600 por mil têm prior igual; posterior exato por contagem de mudanças e permanências. A decisão de pit usa apenas prefixo observado. Comparar heurística, Bellman com taxa fixa 350 por mil, Bellman Bayesiano e limite inferior com regime conhecido. Enumerar 256 sequências de oito voltas, medir custo esperado e Brier das previsões de mudança (menor é melhor). A amostra independente usa seed 20261128, 32 casos por taxa 100/600/900, incluindo regime fora do prior; ranking amostral exploratório. Dominância e Brier exatos somente sob distribuição assumida. Sem radar real, intensidade de chuva, previsão meteorológica operacional ou integração esportiva.

## Multi-Stint Strategy Intelligence 0.9.3

Estado: voltas restantes, pneu, idade, clima observado, contagem de mudanças/permanências e número de pits realizados. Ações aguardar, trocar para seco ou molhado; entre um e três pits antes de voltas distintas. Empates favorecem aguardar, depois seco e molhado. Reutiliza custos artificiais de 0.9.0 e posterior 0.9.2 sem alterar os experimentos anteriores. Comparar valor esperado de um pit com referência anterior (empates podem mudar a trajetória) e de até três pits em 256 sequências ponderadas. Oráculo retrospectivo independente enumera planos completos somente para avaliação. Amostra seed 20261129, 24 casos por regime 100/600/900. Oito critérios zero, ranking amostral exploratório. Não há inventário, limite regulamentar real, compostos slick distintos, tráfego, desgaste calibrado ou integração.

### Resultado e cobertura adicional

A candidata inicial (e6c34284747b54032cdd6ab24189387017b98575, run 46079717651) retornou PASS em todos os oito critérios; custo esperado idêntico 768841,0201 ms e uma parada em todas as 72 amostras. O fixture original não demonstra benefício de múltiplas paradas. Preservado sem alterações. Testes adicionais de cobertura verificam replays com duas/três paradas obrigatórias em todas as sequências de quatro voltas e a decisão opcional de parada adicional em estado condicional sintético de pneu gasto e clima persistente. Esses estados não são novas amostras de desempenho, não representam a trajetória original e não alteram o gate experimental.

## Tyre Degradation Intelligence 0.9.4

Novo modelo isolado: custo por volta em ms = 90000 + offset + slope*idade + curva*max(0,idade-cliff)^2 + penalidade de incompatibilidade climática de 8000. Perfis artificiais (offset, slope, cliff, curva): soft (0,220,5,750), medium (350,150,8,450), hard (850,90,12,250), wet (500,130,8,350). Idade em voltas completadas, não desgaste físico medido. Pneu inicial medium idade 4, pit 24000 ms. Comparar um vs até três pits sob custos idênticos; posterior 0.9.2, 256 sequências de oito voltas ponderadas e 72 episódios separados de doze voltas (24 por taxa 100/600/900, seed 20261130). Critérios congelados: zero erros de curva, causalidade, peso, Bellman, dominância esperada, legalidade/contabilidade, replay e regret negativo. Oráculo de segmentos retrospectivo independente, testado por enumeração curta. Nenhum ajuste após observar resultados; ranking amostral exploratório. Não é modelo térmico de physics_tyre, não representa compostos históricos reais nem substitui o motor oficial.

## Undercut & Overcut Intelligence 0.9.5

Janela seca de quatro voltas, um pit antes de uma volta, três slicks artificiais da 0.9.4. Rival exógeno para na volta de índice 1 ou 2 (zero-based), soft, ritmo ±500 ms/volta, quatro hipóteses equiprováveis fixas. Classificação de undercut/overcut relativa ao pit realizado do rival, não garantia de ultrapassagem. Rank de saída e chegada por ordem temporal na mesma fronteira de distância; não é posição instantânea. Tráfego exógeno: carro que cruzou até 2000 ms antes da saída implica perda fixa de 1500 ms na volta de saída; empate desfavorável. Comparação solo (menor tempo sem tráfego) vs duelo (minimiza contagem de derrotas, soma de gaps, tempo próprio, desempate por índice). Escolha antes de sortear rival realizado. Grid 24 estados × 12 planos × 4 hipóteses, 96 casos amostrais seed 20261201. Seis critérios de contrato, não superioridade amostral. Sem física de ultrapassagem, reação adversária, pit queue ou integração esportiva. REF-106 e ideias do portfólio, nenhum código externo copiado.

### Auditoria corretiva da candidata

Carros de fundo distintos podem cruzar no mesmo milissegundo; offsets continuam ordenados, mas repetições são permitidas. Empates de chegada são não-vitórias e a ordem estimada é conservadora. O atraso permanece único e limitado. Uma referência independente por somas de segmentos verifica tempos próprio e rival, saída, gap, tráfego, ranks e ótimo de todos os planos no grid original e na amostra. Cinco testes adicionais cobrem empates, entradas inválidas, extremos de domínio e detecção de erros injetados. Seed, amostra, parâmetros e seis limiares congelados permanecem. Sem alegação de calibração ou promoção esportiva.

## Pit Window Intelligence 0.9.6

Janela de quatro voltas a partir de snapshot observado, 0 ou 1 pit próprio conforme obrigação, quatro compostos sintéticos. Restrições de índice inicial/final e trava manual de volta; a trava não é cancelada por chuva. Posterior de 0.9.2 (taxas 100/600 por mil), oito caminhos futuros × quatro hipóteses rivais de 0.9.5, pesos inteiros exatos. Minimiza gap esperado; primeira/última volta delimitam conjunto discreto de alternativas até 1000 ms do ótimo (não implicam continuidade). Ideal pode ser nenhuma parada; probabilidade de ficar até 1000 ms do melhor plano retrospectivo é condicional ao modelo, não confiança calibrada. Baseline fixa pit no meio da janela, com composto baseado no clima observado. 32 estados × até 17 planos × 32 hipóteses, 96 casos pareados seed 20261202, sete critérios zero e nove testes. Oráculo independente por segmentos; amostra exploratória inclui taxa 900 fora do prior. Recalcular com novo snapshot; não é replay adaptativo integral, não há fila, inventário, reação rival ou integração esportiva.

## Traffic Prediction Intelligence 0.9.7

Extensão isolada da janela 0.9.6. Carros de fundo possuem composto, idade e ritmo exógenos; rival mantém prior 0.9.5. A cada fronteira de volta, carros à frente mais lentos produzem pressão proporcional à vantagem de ritmo e proximidade prevista (janela 2000 ms). Perda compartilhada: maior pressão em ms + 250 ms por carro adicional afetado, limitada à maior vantagem e 3000 ms/volta. Sem soma de perdas individuais; atraso propagado nas próximas voltas, inclusive para planos sem parada. Ar limpo significa ausência de pressão temporal modelada, não medição aerodinâmica. Comparar seleção de 0.9.6 com seleção do novo proxy em mesmo ambiente variável. 32 estados × até 17 planos × 32 hipóteses; 64 casos pareados, seed 20261203, oito critérios zero e oito testes. Referência racional da pressão, contabilidade independente de segmentos limpos e invariância de ordem. Ranking exploratório, sem interação recíproca, posição física, calibração ou promoção esportiva. Código original.
