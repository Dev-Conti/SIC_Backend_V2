DECLARE @DataInicio DATE = '2025-01-01';   
DECLARE @DataFim DATE = '2025-01-31';       

SELECT
    CAST(aus.AUST_ID AS VARCHAR) AS AUST_ID,
    RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(usu.CPF, '.', ''), '-', ''), ' ', ''), 11) AS CPF,
    -- Se DT_INICIO for menor que @DataInicio, substituímos por @DataInicio
    -- Senão, mantemos a data original
    CONVERT(VARCHAR(10), 
        CASE 
            WHEN aus.DT_INICIO < @DataInicio THEN @DataInicio 
            ELSE aus.DT_INICIO 
        END, 120) AS DT_INICIO_AJUSTADO,
    -- Se DT_FIM for maior que @DataFim, substituímos por @DataFim
    -- Senão, mantemos a data original
    CONVERT(VARCHAR(10), 
        CASE 
            WHEN aus.DT_FIM > @DataFim THEN @DataFim 
            ELSE aus.DT_FIM 
        END, 120) AS DT_FIM_AJUSTADO
FROM
    pso_usuarios usu
    INNER JOIN pso_centros_resultado cr ON cr.CR_ID = usu.CR_ID
    LEFT JOIN pso_ausencias aus ON usu.USU_ID = aus.USU_ID
WHERE
    cr.CR_ID = usu.CR_ID
    AND (aus.aust_id = '1' OR aus.aust_id IS NULL OR aus.aust_id = '')
    AND usu.UDF10 = 'Sim'
    AND usu.UDF6 = 'Ativo'
    AND (
        -- Caso 1: A data de início esteja dentro do intervalo
        aus.DT_INICIO BETWEEN @DataInicio AND @DataFim
        -- Caso 2: A data de fim esteja dentro do intervalo
        OR aus.DT_FIM BETWEEN @DataInicio AND @DataFim
        -- Caso 3: A ausência começa antes e termina depois do intervalo
        OR (aus.DT_INICIO <= @DataInicio AND aus.DT_FIM >= @DataFim)
    );
