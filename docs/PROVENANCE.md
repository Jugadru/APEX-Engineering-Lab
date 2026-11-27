# Scientific Evidence Registry 0.2.0

O registro v1 de plano e resultado permanece compatível. A v0.2 acrescenta declaração lateral exclusiva e vinculada ao hash do resultado. O usuário registra a origem (synthetic, local ou github_actions), a execução declarada e os arquivos ZIP correspondentes. Não confundir declaração com autenticação.

## Operação

Após plan/record, use o hash result_sha256 retornado e preencha examples/provenance.json com os valores reais. O comando declare não executa nem consulta a rede.

```sh
python -m engineering_lab declare declaration.json --registry /tmp/apex-research
python -m engineering_lab provenance --registry /tmp/apex-research --id EXP-EXAMPLE-001
# Somente se a origem declarada for github_actions e o acesso público for desejado:
python -m engineering_lab github-check --registry /tmp/apex-research --id EXP-EXAMPLE-001
python -m engineering_lab github-receipt --registry /tmp/apex-research --id EXP-EXAMPLE-001
python -m engineering_lab receipt --registry /tmp/apex-research --id EXP-EXAMPLE-001
```

O adapter GitHub lê HTTPS em api.github.com, sem token, sem redirecionamento, com timeout de 10 s por consulta, máximo 1 MiB por resposta e allowlist fixa: Simulation, Hyper Engine, Engineering Lab. Confere SHA candidato, SHA Lab, baseline se presente, repo de origem, run ID, tentativa atual, estado final e SHA head. Rejeita fork, run não concluído, SHA divergente e arquivos expirados ou sem digest. A tentativa é a atual; reexecuções posteriores invalidam o vínculo anterior. Não baixa nem extrai ZIPs; se houver mapeamentos, confira o digest SHA-256 do arquivo ZIP intacto registrado como evidência com os metadados do artifact. Digests ausentes bloqueiam a verificação. API de artifacts não prova a tentativa específica de criação do ZIP; os metadados do run não certificam conteúdo de métricas ou que o código Lab foi executado. Sem rede, limite de API, acesso privado ou divergência: BLOCKED, nunca PASS fabricado.

## Níveis de evidência e maturidade

- DECLARED_ONLY: declaração local, sem comprovação da origem.
- PUBLIC_GITHUB_METADATA_MATCH: consulta HTTPS atual corresponde aos metadados; não é assinatura nem atestado de execução científica.
- archive_digest_coverage NONE/PARTIAL/ALL: cobertura de arquivos registrados pelos digests de ZIPs reportados pelo GitHub, nunca inferir conteúdo.
- PROPOSTO (NOT_RUN) ou EXPERIMENTAL (demais resultados): maturidade conservadora. EVIDENCE_FOR_REVIEW sinaliza cobertura total, workflow success e resultado decisivo; não é aprovação. VALIDADO_EM_ESCOPO, CANDIDATO_INTEGRACAO e INTEGRADO dependem de revisão externa e ficam indisponíveis nesta versão.
- scientific_review NOT_PERFORMED; promotion NOT_AUTHORIZED em todos os casos.

github-receipt salva um snapshot exclusivo e não assinado da consulta; receipt revalida vínculos e bytes locais, mas sempre declara LOCAL_SNAPSHOT_UNAUTHENTICATED e exige consulta ao vivo para confirmar a origem. Não é ledger inviolável, assinatura, timestamp confiável ou prova de autoridade. O status experimental e o resultado do workflow são independentes. Resultado sintético jamais é promovido. Nenhum adapter dispara workflows ou altera repositórios.

## Escopo

CI usa fixtures sintéticas para o adapter, sem rede, e mantém os testes v1. Verificação ao vivo é opt-in. Adapters específicos de Foundation, Asset Factory, Hyper e Lab Hub continuam pendentes: o adapter GitHub é compartilhado, não duplica profilers. Evidências privadas não são publicadas; o repositório foi tornado privado pelo responsável. Nenhum runner pessoal, FULL ou mudança no jogo. Limite local de 1 MiB mantido. Revisão de assinatura/proveniência criptográfica, autorização e ciência continua futura.

**v0.3:** Engineering Lab e Hyper privados. Adapter sem autenticação fica BLOCKED em revisões privadas. Usar conector autorizado para revisão manual; sem tokens novos.
