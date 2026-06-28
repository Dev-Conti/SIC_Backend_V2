DECLARE @DataInicio DATE = :data_inicio;   -- Usando parâmetro
DECLARE @DataFim DATE = :data_fim;         -- Usando parâmetro

SELECT
    CAST(aus.AUST_ID AS VARCHAR) AS AUST_ID,
    RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(usu.CPF, '.', ''), '-', ''), ' ', ''), 11) AS CPF,
    CONVERT(VARCHAR(10), aus.DT_INICIO, 120) AS DT_INICIO,
    CONVERT(VARCHAR(10), aus.DT_FIM, 120) AS DT_FIM
FROM
    pso_usuarios usu
    INNER JOIN pso_centros_resultado cr ON cr.CR_ID = usu.CR_ID
    LEFT JOIN pso_ausencias aus ON usu.USU_ID = aus.USU_ID
WHERE
    cr.CR_ID = usu.CR_ID
    AND (aus.aust_id = '1' OR aus.aust_id IS NULL OR aus.aust_id = '')
    AND usu.UDF10 = 'Sim'
    AND usu.UDF6 = 'Ativo'
    AND aus.DT_INICIO >= @DataInicio
    AND aus.DT_FIM <= @DataFim;
