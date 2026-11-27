# Strategy Research Lab

**Estado:** 0.9.2 homologada; 0.9.3 múltiplos stints em candidata até aprovação CI.

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
