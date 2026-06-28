DECLARE @cpf VARCHAR(11);
SET @cpf = :cpf ; -- CPF apenas com números

DECLARE @usu_id INT;

-- Validar CPF de entrada
IF LEN(@cpf) = 11 AND @cpf NOT LIKE '%[^0-9]%'  
BEGIN
    SELECT @usu_id = usu_id
    FROM pso_usuarios
    WHERE LEN(REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '')) = 11  -- Garante CPF válido no banco
    AND REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = @cpf;

    SELECT @usu_id AS UsuarioID;
END
ELSE
BEGIN
    PRINT 'CPF inválido: deve conter exatamente 11 dígitos numéricos.';
    SELECT NULL AS UsuarioID;
END
