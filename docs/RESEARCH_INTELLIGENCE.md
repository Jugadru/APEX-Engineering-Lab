# Research Intelligence v0.3.0

## Foundation
O catálogo soberano está no [APEX-Foundation](https://github.com/Jugadru/APEX-Foundation), commit c999d8f4062d2df07f1deae55a2252f6262596bf: 198 REF e 120 IDEA. O pin conserva SHAs Git blob e contagens, não duplica catálogo. O conector conferiu as associações reais durante a preparação. Forneça cópia autorizada dos dois JSON exatos de docs/references, sem conversão de newline; não enviar catálogo privado para APIs públicas. O pin não é assinatura criptográfica.

## Operação
```sh
python -m engineering_lab research-rank
python -m engineering_lab research-validate --foundation-dir /path/to/APEX-Foundation/docs/references
python -m engineering_lab research-search "torque" --foundation-dir /path/to/APEX-Foundation/docs/references
python -m engineering_lab research-discover github "lap time simulation"
python -m engineering_lab research-discover crossref "motorsport pit strategy"
```
Discovery é opt-in, envia somente a consulta explícita ao GitHub/Crossref (use termos públicos, nunca informação privada), até 5 resultados, 10 s timeout, 1 MiB, sem redirecionamentos, tokens ou execução. Resultados são candidatos. CI testa fixtures offline; transporte ao vivo não homologado.

Para proposta, use research-propose --foundation-dir PATH --card RES-001 --id EXP-RESEARCH-001 --repository Jugadru/APEX-Engineering-Lab --candidate SHA --lab SHA --baseline SHA --registry PATH. Substitua por SHAs reais e diretório local existente. Gera plano v1 exclusivo, não resultado, código ou execução. Antes da execução elaborar parâmetros/ordem de comandos e registrar novo plano definitivo. Não alterar critérios congelados. Nenhuma corrida ou benchmark autorizado por uma proposta.

## Carteira
Cinco propostas, quatro fontes com metadados e LICENSE raiz revisados no commit exato. Artigo VSE 2020 consultado; demais DOIs são indicações bibliográficas de upstream, não leitura integral. Nenhum código, peso, dataset ou asset importado. Copiar/adaptar bloqueado até revisão por arquivo, dependências, assets, compatibilidade e autorização. Rótulo SPDX do GitHub não resolve todos os termos.

Score ordinal = 2*benefício - custo - risco (1–5), estimativas, não desempenho medido. Complexidade teórica estimada, não perfil do APEX. Inventário do jogo em 9dfc18de49083260b1a9524513b415e1551fdabf e Roadmap 3.0: nomes e roadmap indicam cobertura parcial, não auditoria semântica nem lacuna comprovada. Auditar módulos existentes antes de propor mudanças. Ordem do roadmap do jogo preservada.

## Privacidade
Engineering Lab, Foundation, Hyper, Asset Factory e Hub privados. Adapter v0.2 público fica BLOCKED ao consultar commit privado; revisão manual por conector autorizado. Adapter autenticado futuro com credenciais gerenciadas, não tokens pessoais no chat. Nenhum runner pessoal, FULL, benchmark pesado ou integração automática.
