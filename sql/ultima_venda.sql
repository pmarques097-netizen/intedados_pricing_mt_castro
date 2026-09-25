WITH ultimas_vendas AS (
    SELECT DISTINCT ON (
        iv.unidadenegocioid,
        iv.embalagemid
    )
        iv.unidadenegocioid,
        iv.embalagemid,
        iv.datahora,
        iv.quantidade,
        iv.valorunitario,
        iv.valortotal,
        iv.vendaid

    FROM public.itemvenda iv

    JOIN public.venda v
        ON v.id = iv.vendaid

    WHERE iv.status = 'F'
      AND v.status = 'F'
      AND iv.quantidade > 0

    ORDER BY
        iv.unidadenegocioid,
        iv.embalagemid,
        iv.datahora DESC,
        iv.vendaid DESC
)

SELECT
    un.nome AS loja,
    p.codigo AS cod_interno,
    e.codigobarras AS ean,
    e.descricao AS produto,

    uv.datahora AS data_ultima_venda,

    ROUND(
        uv.valortotal / NULLIF(uv.quantidade, 0),
        2
    ) AS ultimo_preco_vendido,

    uv.quantidade,
    uv.valorunitario AS preco_tabela,
    uv.valortotal AS valor_total,
    uv.vendaid

FROM ultimas_vendas uv

JOIN public.embalagem e
    ON e.id = uv.embalagemid

LEFT JOIN public.produto p
    ON p.id = e.produtoid

LEFT JOIN public.unidadenegocio un
    ON un.id = uv.unidadenegocioid

ORDER BY
    un.nome,
    e.descricao;