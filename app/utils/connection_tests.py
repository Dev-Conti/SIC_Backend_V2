from ..extensions import mongo, redis_client, db_psoffice

def test_mongo_connection():
    """Função para testar a conexão com o MongoDB."""
    try:
        # Verifica se consegue acessar o banco 'admin'
        mongo.cx.admin.command('ping')
        print("Conexão com o MongoDB bem-sucedida!")
        return "Conexão com o MongoDB bem-sucedida!"
    except Exception as e:
        error_message = f"Erro ao conectar ao MongoDB: {e}"
        print(error_message)
        return error_message

def test_redis_connection():
    """Função para testar a conexão com o Redis."""
    try:
        # Verifica se consegue acessar o Redis
        redis_client.client.ping()
        print("Conexão com o Redis bem-sucedida!")
        return "Conexão com o Redis bem-sucedida!"
    except Exception as e:
        error_message = f"Erro ao conectar ao Redis: {e}"
        print(error_message)
        return error_message

def test_db_psoffice_connection():
    """Função para testar a conexão com o banco de dados Psoffice."""
    try:
        db_psoffice.connect()
        print("Conexão com o banco de dados Psoffice bem-sucedida!")
        db_psoffice.close()
        return "Conexão com o banco de dados Psoffice bem-sucedida!"
    except Exception as e:
        error_message = f"Erro ao conectar ao banco de dados Psoffice: {e}"
        print(error_message)
        return error_message
