# asset_factory — v1

**Entrada:** ID do job, revisão, orçamento, origem e licença no relatório externo.

**Saída:** hash e QA de artefato em staging; sem promover assets; não copiar pipeline existente.

**Estado:** contrato documental e envelope comum; adapter e autenticação remota NOT_RUN. Rejeitar SHA divergente, métricas inválidas e critérios não congelados. Autoridade permanece no sistema de origem. Sem segredos ou dados privados no envelope público.
