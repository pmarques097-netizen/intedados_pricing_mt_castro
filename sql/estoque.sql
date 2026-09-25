select
	case
		when p.status = 'A' then 'ATIVO'
		when p.status = 'I' then 'INATIVO'
	end as status_produto,
	uni.codigo as num_loja,
	p.codigo as cod_int,
	emb.etiqueta,
	emb.codigobarras as cod_barras,
	emb_contida.codigobarras as embalagem_filha,
	emb.quantidadeporembalagem as qtd_por_embalagem,
	emb.padraofornecedores as principal,
	p.descricao,	
	case 
        when c.caminho like 'PRINCIPAL > 1%' then '1-ETICO'
        when c.caminho like 'PRINCIPAL > 2%' then '2-GENERICOS'
        when c.caminho like 'PRINCIPAL > 3%' then '3-SIMILARES'
        when c.caminho like 'PRINCIPAL > 4%' then '4-DIAMANTES'
        when c.caminho like 'PRINCIPAL > 5%' then '5-PERFUMARIA'
        when c.caminho like 'PRINCIPAL > 6%' then '6-CONVENIENCIA'
        when c.caminho like 'PRINCIPAL > 7%' then '7-LEITES E FRALDAS'
        when c.caminho like 'PRINCIPAL > 8%' then '8-SERVICOS'
        when c.caminho like 'PRINCIPAL > 9%' then '9-USO CONSUMO'
        else 'Outro'
    end as classificao,
    translate(c.caminho, 'áàãâäéèêëíìîïóòõôöúùûüçÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇ', 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC') AS classificacao_geral,
    pe.razaosocial as fabricante,
    cabc.nome as curva,
    (custo_p.custo)::numeric(18,4) as custo_unit_atual,
    (custo_p.customedio)::numeric(18,4) as custo_medio_atual,
		est.estoque as estoque	
from produto p
left join curvaabcproduto as cpabc on cpabc.produtoid = p.id
left join curvaabc as cabc on cabc.id = cpabc.curvaabcvalorid
left join embalagem as emb on emb.produtoid = p.id
left join embalagem AS emb_contida ON emb_contida.id = emb.embalagemcontidaid
left join estoque as est on est.embalagemid = emb.id
left join unidadenegocio as uni on uni.id = est.unidadenegocioid
LEFT JOIN fabricante AS f ON f.id = p.fabricanteid
LEFT JOIN pessoa AS pe ON pe.id = f.pessoaid
left join classificacaoproduto AS cp ON cp.produtoid = p.id
left join classificacao AS c ON c.id = cp.classificacaoid
left join (
    select distinct on (c.produtoid, c.unidadenegocioid)
        c.produtoid,
        c.unidadenegocioid,
        c.custo,
        c.customedio
    from custoproduto c
    order by c.produtoid, c.unidadenegocioid, c.id desc  -- Pegando o custo mais recente
) as custo_p on custo_p.produtoid = p.id and custo_p.unidadenegocioid = uni.id
where uni.codigo not in ('14-2','20', '21', '25', '26', '40', '41', 'BKP', 'CLOUD', 'ESC')
and c.caminho ilike '%PRINCIPAL%'
and c.caminho not in ('PRINCIPAL > 8 - SERVICOS > SERVICOS', 'PRINCIPAL > 8 - SERVICOS > TAXA DE ENTREGA', 'PRINCIPAL > 9 - USO CONSUMO > USO CONSUMO', 'PRINCIPAL > 9 - USO CONSUMO > USO E CONSUMO')
group by p.status, uni.codigo, p.codigo, emb.etiqueta, emb.codigobarras, emb_contida.codigobarras, p.descricao, pe.razaosocial, cabc.nome, c.caminho, est.estoque, custo_p.custo, custo_p.customedio, emb.quantidadeporembalagem, emb.padraofornecedores
