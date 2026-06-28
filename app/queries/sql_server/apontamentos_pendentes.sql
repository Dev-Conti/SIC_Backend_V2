DECLARE @DataInicio DATE = :data_inicio;   -- Usando parâmetro
DECLARE @DataFim DATE = :data_fim;  
DECLARE @CPF VARCHAR(11) = :cpf;        -- Usando parâmetro

SELECT 
    CAST(a.APON_ID AS VARCHAR) AS APON_ID,
    CAST(a.PROJ_ID AS VARCHAR) AS PROJ_ID,
    CAST(a.USU_ID AS VARCHAR) AS USU_ID,
    p.codigo AS PROJETO,
    RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(u.CPF, '.', ''), '-', ''), ' ', ''), 11) AS CPF,
    CONVERT(VARCHAR, a.DT_INICIO, 23) AS DT_INICIO, -- Formato YYYY-MM-DD
    FORMAT(a.MINUTOS / 60.0, 'N2') AS HORAS, -- Convertendo minutos em horas com duas casas decimais
    FORMAT(a.MINUTOS_REC_EXT / 60.0, 'N2') AS HORAS_REC_EXT, -- Convertendo minutos em horas com duas casas decimais
    CAST(a.STATUS AS VARCHAR) AS STATUS

FROM pso_apontamentos a
JOIN pso_usuarios u ON a.USU_ID = u.USU_ID
JOIN pso_projetos p ON a.PROJ_ID = p.PROJ_ID -- JOIN permanece o mesmo
WHERE STATUS IN ('0', '1', '4')
  AND a.DT_INICIO BETWEEN @DataInicio AND @DataFim
  AND (RIGHT('00000000000' + REPLACE(REPLACE(REPLACE(u.CPF, '.', ''), '-', ''), ' ', ''), 11) = @CPF OR @CPF IS NULL OR @CPF = '')
ORDER BY a.DT_INICIO