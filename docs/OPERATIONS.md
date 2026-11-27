# Operação e segurança

Python 3.10+; CLI offline sem dependências. Usar diretório privado de registro fora do Git; não compartilhar artefatos confidenciais. Planos e resultados exclusivos por ID, arquivos até 1 MiB, artefatos até 1 MiB nesta versão. Hash canônico JSON ordenado, UTF-8 ASCII escapado e sem NaN. Artefatos são arquivos diretos no diretório artifacts do registro, não caminhos arbitrários. Apenas sistema de arquivos local confiável; não é sandbox hostil nem ledger autenticado.

```sh
mkdir -m 700 /tmp/apex-research
mkdir -m 700 /tmp/apex-research/artifacts
python3 -m engineering_lab plan examples/plan.json --registry /tmp/apex-research
# Execute a investigação autorizada separadamente e deposite o artefato.
python3 -m engineering_lab record result.json --registry /tmp/apex-research
python3 -m engineering_lab verify --registry /tmp/apex-research --id EXP-EXAMPLE-001
```

O exemplo de plano contém SHAs fictícios e não prova execução. O demo cria seus próprios resultados sintéticos. CI hospedada com token contents:read, sem runner pessoal e sem checkout de repositórios privados. Workflow dispara em PR/push main; timeout de 5 min. Não há credenciais novas nem agente residente. O registro não executa experimentos arbitrários.

Para ferramentas externas: GitHub com leitura/escrita conforme repo; Godot 4.7.2 para regressões do jogo; Blender para Asset Factory; GPU nativa e runner pessoal somente após consentimento e ociosidade. Não solicitar tokens. Limites de depuração em AGENTS são política, não scheduler. Backup local e revisão de licença obrigatórios. Rollback da fundação via revert do commit/PR, sem apagar evidências.
