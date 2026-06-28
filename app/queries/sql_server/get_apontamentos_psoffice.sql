DECLARE @DataInicio DATE = :data_inicio;   -- Usando parâmetro
DECLARE @DataFim DATE = :data_fim;         -- Usando parâmetro

SELECT 
    CAST(a.APON_ID AS VARCHAR) AS APON_ID,
    CAST(a.USU_ID AS VARCHAR) AS USU_ID,
    CONVERT(VARCHAR, a.DT_INICIO, 23) AS DT_INICIO, -- Formato YYYY-MM-DD
    CAST(a.MINUTOS AS VARCHAR) AS MINUTOS,
    CAST(a.PROJ_ID AS VARCHAR) AS PROJ_ID,
    CAST(a.STATUS AS VARCHAR) AS STATUS,
    RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(u.CPF, '.', ''), '-', ''), ' ', ''), 11) AS CPF
FROM pso_apontamentos a
JOIN pso_usuarios u ON a.USU_ID = u.USU_ID
WHERE STATUS = '2' AND a.DT_INICIO BETWEEN @DataInicio AND @DataFim
ORDER BY a.DT_INICIO;
