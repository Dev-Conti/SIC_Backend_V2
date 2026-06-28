from flask import jsonify, request, current_app
from app.utils.decorators import require_auth  # Use o nome correto da função
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_tokens
from .services import get_warmup_projetos_collection, get_warmup_projeto_by_id, iniciar_warmup, atualizar_warmup  # Importar a nova função
from . import warmup_bp
from bson import ObjectId
from app.utils.serialization import serialize_mongo_documents

@warmup_bp.route('/', methods=['GET'])
def warmui():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota warmup implantada com sucesso!", {"status": "online"})

@warmup_bp.route('/listar', methods=['GET'])
def get_warmup():
    """Endpoint para retornar os dados da coleção warmup_projetos."""
    try:
        etapa = request.args.get('etapa')  # Obter o parâmetro 'etapa' da query string
        documents = get_warmup_projetos_collection(etapa)  # Obter lista de documentos diretamente
        data = serialize_mongo_documents(documents)  # Serializar lista de documentos
        return success_response("Dados recuperados com sucesso.", data)
    except Exception as e:
        return error_response(f"Erro ao recuperar dados: {e}")

@warmup_bp.route('/listar/<id>', methods=['GET'])
def get_warmup_id(id):
    """Endpoint para retornar um único documento da coleção warmup_projetos pelo ID."""
    try:
        document = get_warmup_projeto_by_id(id)
        if document:
            data = serialize_mongo_documents([document])  # Serializar o documento
            return success_response("Documento recuperado com sucesso.", data[0])
        else:
            return error_response("Documento não encontrado.", 404)
    except Exception as e:
        return error_response(f"Erro ao recuperar documento: {e}")

@warmup_bp.route('/processar_dados', methods=['POST'])
def processar_dados():
    """Endpoint para processar e inserir dados na coleção warmup_projetos."""
    try:
        dados = request.get_json()
        current_app.logger.debug(f"Payload recebido: {dados}")

        if not dados:
            return jsonify({"status": "error", "message": "Nenhum dado enviado."}), 400

        document_id = iniciar_warmup(dados)
        current_app.logger.debug(f"Resultado da inserção: {document_id}")

        return jsonify({
            "status": "success",
            "message": "Dados inseridos com sucesso.",
            "document_id": document_id
        }), 201

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Erro ao processar dados: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@warmup_bp.route('/atualizar/<negocio_id>', methods=['PUT'])
def atualizar_warmup_route(negocio_id):
    dados = request.json
    if '_id' in dados:
        del dados['_id']  # Remove the _id field from the payload
    modified_count = atualizar_warmup(negocio_id, dados)
    if modified_count:
        return jsonify({"message": "Documento atualizado com sucesso"}), 200
    else:
        return jsonify({"message": "Nenhum documento foi atualizado"}), 404


