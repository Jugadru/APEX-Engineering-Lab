# APEX Engineering Lab

Autonomous scientific research, experimental engineering, algorithm development and computational intelligence infrastructure for the APEX Motorsport ecosystem.

**v0.6.5 — Scientific Experiment Reports**

Laboratório de P&D independente do motor oficial e do Development Lab. Pesquisa científica, modelos isolados, comparação de algoritmos e evidência reproduzível. Não é outro motor nem outro sistema de homologação.

## Começar

Python 3.10+ (biblioteca padrão, sem instalação de dependências):

```sh
python3 -m unittest discover -s tests -v
python3 -m engineering_lab demo --registry /tmp/apex-engineering-demo-new
python3 -m engineering_lab verify --registry /tmp/apex-engineering-demo-new --id EXP-DEMO-001
```

O demo executa uma hipótese aritmética sintética, não uma corrida. Cria plano antes da observação, registra um artefato local e confere SHA-256. A pasta do demo deve ser nova. O comando verify valida a consistência e os bytes do artefato; não certifica autenticidade científica, autorização ou desempenho do jogo.

## Navegação

- [AGENTS.md](AGENTS.md): autoridade e regras permanentes.
- [Roadmap](ROADMAP.md): sequência de capacidades, sem substituir os roadmaps Core 2/Hyper.
- [Departamentos](departments/README.md): 12 áreas e critérios.
- [Experimental Engineering](docs/EXPERIMENTAL_ENGINEERING.md): bounded executable prototypes.
- [Autonomous Debugging](docs/AUTONOMOUS_DEBUGGING.md): investigations and evidence lifecycle.
- [Code Intelligence](docs/CODE_INTELLIGENCE.md): existing diagnostic outputs, dependency impact and static review.
- [Research Intelligence](docs/RESEARCH_INTELLIGENCE.md): carteira, licenças, Foundation pin e propostas.
- [Procedência científica](docs/PROVENANCE.md): declarações, metadados GitHub, digests e maturidade conservadora.
- [Contratos](contracts/README.md): Foundation, Asset Factory, Lab Hub, Hyper Engine.
- [Protocolo científico](docs/RESEARCH_PROTOCOL.md) e [Operação](docs/OPERATIONS.md).
- [Auditoria e origem](docs/BASELINE.md), [Changelog](CHANGELOG.md).

## Ecossistema

- [APEX-Simulation](https://github.com/Jugadru/APEX-Simulation): jogo, FAST + APEX Test Lab.
- [APEX-Hyper-Engine](https://github.com/Jugadru/APEX-Hyper-Engine): motor experimental separado.
- Development Lab: diagnóstico e benchmarks existentes, acesso conforme autorização.
- Foundation: catálogo de referência de propriedade do ecossistema; não duplicado aqui.

Repositório privado por decisão do responsável (26/11/2026). Não armazenar logs privados, dados pessoais, credenciais, arquivos de terceiros sem licença ou assets de produção. Nenhum runner pessoal ou serviço permanente é instalado. Sem licença de distribuição escolhida: não presumir permissão de reutilização externa.
