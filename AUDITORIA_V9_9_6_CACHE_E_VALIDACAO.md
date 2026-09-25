# V9.9.6 — Correção de atualização do cache e auditoria de contratos

- A assinatura de arquivos PostgreSQL não é mais cacheada sem chave: cada chamada observa nomes, tamanhos e mtime dos Parquets.
- O carregador PostgreSQL em memória recebe a assinatura como argumento efetivamente hashável, invalidando automaticamente quando os arquivos mudam.
- A atualização dos snapshots também limpa explicitamente o cache do carregador PostgreSQL.
- O gráfico mensal recebe assinatura de cache como argumento efetivamente hashável; continua usando apenas venda_YYYY-MM.parquet e os EANs da ação filtrada.
- As regras, fórmulas e fontes de preço/custo não foram alteradas.

## Testes pendentes para homologação
Testar no Streamlit com PostgreSQL real: atualização de mês e fotografia, troca de rede/cliente, Geral versus Dashboard Geral, totais e linhas de ações, comparação por EAN, mapa e exportações. AST/py_compile não demonstram acerto de cálculo ou renderização.
