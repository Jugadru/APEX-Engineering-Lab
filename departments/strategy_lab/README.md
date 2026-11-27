# Strategy Research Lab

**Estado:** 0.9.0 — primeira capacidade experimental (candidata até aprovação CI).

## Mandato

Monte Carlo, VSE, undercut/overcut, previsão imperfeita, pit windows, double stack e stints.

## Restrições

Comparar heurística simples antes de ML; informação disponível no tick; sem vazamento do futuro.

## Entrega e aceitação

Comparação de estratégias com seeds e incerteza. Toda entrega exige hipótese, critérios prévios, revisão exata, evidência e limitações. Consulte [protocolo](../../docs/RESEARCH_PROTOCOL.md). Não assumir integração automática.

## Primeira capacidade

`strategy_weather_decision`: 32 episódios sintéticos de oito voltas, um pit obrigatório antes de uma volta, dois pneus artificiais, clima binário observado, 32 previsões por decisão. Heurística troca por incompatibilidade ou metade do horizonte; Monte Carlo replaneja com previsão estocástica e informação atual. Os caminhos de previsão são comuns às alternativas e a geração dos episódios de teste usa seed separada. Oráculo retrospectivo somente para avaliação. Critérios pré-declarados: zero ações inválidas, divergências de replay ou regret negativo. Diferença de regret é exploratória, não critério de aprovação. Não é VSE, não simula tráfego, double stack ou pneus reais. Nenhuma integração esportiva autorizada.
