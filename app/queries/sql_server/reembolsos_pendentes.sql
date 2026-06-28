DECLARE @DataInicio DATE = :data_inicio;   -- Usando parâmetro
DECLARE @DataFim DATE = :data_fim;         -- Usando parâmetro

SELECT 
    CAST(a.DESP_ID AS VARCHAR) AS DESP_ID,
    CAST(a.PROJ_ID AS VARCHAR) AS PROJ_ID,
    p.codigo AS PROJETO,
    RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(u.CPF, '.', ''), '-', ''), ' ', ''), 11) AS CPF,
    CONVERT(VARCHAR, a.DT_DATA, 23) AS DT_DATA, -- Formato YYYY-MM-DD
    FORMAT(a.VLR_APTO_RECONHECIDO, 'N2') AS VLR_APTO_RECONHECIDO,
    a.descricao AS DESCRICAO
FROM pso_proj_despesas a
JOIN pso_usuarios u ON a.USU_ID = u.USU_ID
JOIN pso_projetos p ON a.PROJ_ID = p.PROJ_ID
WHERE IND_APROVADO = 'N' AND a.DT_DATA BETWEEN @DataInicio AND @DataFim
ORDER BY a.DT_DATA;
