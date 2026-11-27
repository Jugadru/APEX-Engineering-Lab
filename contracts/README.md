# Contratos v1

Envelope comum implementado em engineering_lab/registry.py: plano com ID, peer, hipótese, fontes, revisão candidata e do Lab, tipo, ambiente, cenário, baseline opcional, seed/ticks/hash de comandos e critérios; resultado com hash do plano, mesmas revisões, métricas, status, artefatos e limitações. Verificação de bytes de arquivos locais não autentica autoria ou execução. Não há transporte de rede ou dispatch.

- [Asset Factory](asset_factory.md)
- [Foundation](foundation.md)
- [Lab Hub](lab_hub.md)
- [Hyper Engine](hyper_engine.md)

## v0.2.0

O adapter comum GitHub verifica metadados públicos de revisões, execução e ZIPs registrados. É opt-in e não faz dispatch. Os contratos individuais continuam documentais; ver [proveniência](../docs/PROVENANCE.md).
