from bson.objectid import ObjectId
from datetime import datetime
from app.utils.responses import success_response, error_response
from app.utils.serialization import serialize_mongo_documents
from app.utils.datetime_util import convert_utc_to_timezone

class ChamadosSuporte:
    def __init__(self, mongo_instance):
        self.collection = mongo_instance.db.chamados

    def criar_chamado(self, dados):
        """Cria um novo chamado no banco de dados."""
        try:
            # Converte a string de data em um objeto Date
            if 'dataAbertura' in dados:
                dados['dataAbertura'] = datetime.fromisoformat(dados['dataAbertura'])
            result = self.collection.insert_one(dados)
            return success_response("Chamado criado com sucesso.", {"chamado_id": str(result.inserted_id)})
        except Exception as e:
            return error_response(f"Erro ao criar chamado: {e}")

    def listar_chamados(self):
        """Lista todos os chamados no banco de dados."""
        try:
            chamados = list(self.collection.find())
            for chamado in chamados:
                chamado['_id'] = str(chamado['_id'])  # Converte ObjectId para string
                if 'dataAbertura' in chamado:
                    chamado['dataAbertura'] = convert_utc_to_timezone(chamado['dataAbertura'], 'America/Sao_Paulo')
            return success_response("Chamados listados com sucesso.", {"chamados": chamados})
        except Exception as e:
            return error_response(f"Erro ao listar chamados: {e}")

    def listar_chamado_unico(self, chamado_id):
        """Lista um único chamado pelo ID."""
        try:
            chamado = self.collection.find_one({"_id": ObjectId(chamado_id)})
            if chamado:
                chamado = serialize_mongo_documents([chamado])[0]  # Serializa o documento
                return success_response("Chamado encontrado com sucesso.", {"chamado": chamado})
            else:
                return error_response("Chamado não encontrado.")
        except Exception as e:
            return error_response(f"Erro ao listar chamado: {e}")

    def editar_chamado(self, chamado_id, dados):
        """Edita um chamado existente pelo ID."""
        try:
            result = self.collection.update_one({"_id": ObjectId(chamado_id)}, {"$set": dados})
            if result.modified_count > 0:
                return success_response("Chamado editado com sucesso.")
            else:
                return error_response("Nenhuma modificação realizada.")
        except Exception as e:
            return error_response(f"Erro ao editar chamado: {e}")

    def deletar_chamado(self, chamado_id):
        """Deleta um chamado existente pelo ID."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(chamado_id)})
            if result.deleted_count > 0:
                return success_response("Chamado deletado com sucesso.")
            else:
                return error_response("Chamado não encontrado.")
        except Exception as e:
            return error_response(f"Erro ao deletar chamado: {e}")
