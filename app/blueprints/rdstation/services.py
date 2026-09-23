from app.extensions import mongo
from app.config import Config
import requests
from typing import Optional, Dict, List

config = Config()

class RdServices:
    def __init__(self):
        self.config = Config()
        self.token = self.config.TOKEN_RD

    def obter_empresas(self):
        base_url = "https://crm.rdstation.com/api/v1"
        headers = {"accept": "application/json"}
        page = 1
        limit = 200
        offset = True
        dados = []


        try:
            while offset:
                url = f"{base_url}/organizations?token={self.token}&page={page}&limit={limit}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        dados.extend(data)
                    else:
                        dados.extend(data.get('organizations', []))
                    
                    # Verifica se há mais páginas para buscar
                    offset = data.get('has_more', False)
                    page += 1
                    
                else:
                    return response

            # Retorna os dados exportados
            return dados
        
        except Exception as e:
            print(f"Ocorreu um erro ao exportar negociações: {e}")
            return None

    def obter_pipelines(self):
        base_url = "https://crm.rdstation.com/api/v1"
        headers = {"accept": "application/json"}
        page = 1
        limit = 200
        offset = True
        dados = []

        try:
            while offset:
                url = f"{base_url}/deal_pipelines?token={self.token}&limit={limit}&page={page}"
                response = requests.get(url, headers=headers)
                data = response.json()

                if response.status_code == 200:
                    data = response.json()
                    return data
                
                                        
            # Retorna os dados exportados
            return dados
        except Exception as e:
            return None

    def buscar_deal_por_id(self, negocio_id: str) -> Optional[Dict]:
        """Busca um único deal no RD Station pelo id (`GET /deals/{id}`).

        Usado pela reconciliação de campos: como cada `warmup_projetos` já
        guarda o `negocio_id` (que é o próprio `id` do deal no RD Station),
        não é preciso listar/paginar nada - basta buscar o negócio certo
        diretamente. Retorna `None` (em vez de lançar) se a busca falhar
        (deal excluído no RD Station, erro de rede, etc.), para que quem
        chama possa pular esse negócio sem interromper o processamento dos
        demais.
        """
        base_url = "https://crm.rdstation.com/api/v1"
        headers = {"accept": "application/json"}
        url = f"{base_url}/deals/{negocio_id}?token={self.token}"

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Erro ao buscar deal {negocio_id} no RD Station: {e}")
            return None

    def obter_negociacoes(self, win: Optional[str] = None, closed_at_period: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] =None) -> Optional[List[Dict]]:
        base_url = "https://crm.rdstation.com/api/v1"
        headers = {"accept": "application/json"}
        page = 1
        limit = 200
        offset = True
        dados = []

        try:
            while offset:                
                url = f"{base_url}/deals?token={self.token}&page={page}&limit={limit}"
                if win is not None:
                    win_param = str(win).lower() if isinstance(win, bool) else win
                    url += f"&win={win_param}"
                if closed_at_period is not None:
                    url += f"&closed_at_period={closed_at_period}&start_date={start_date}&end_date={end_date}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        dados.extend(data)
                    else:
                        dados.extend(data.get('deals', []))
                    
                    # Verifica se há mais páginas para buscar
                    offset = data.get('has_more', False)
                    page += 1
                else:
                    break

            # Retorna os dados exportados
            return dados
        except Exception as e:
            print(f"Ocorreu um erro ao exportar negociações: {e}")
            return None

def export_deals(win=None):
    """
    Exporta os dados das negociações do CRM e retorna os dados serializados.
    """
    base_url = "https://crm.rdstation.com/api/v1"
    headers = {"accept": "application/json"}
    page = 1
    limit = 200
    offset = True
    dados = []
    

    try:
        while offset:
            url = f"{base_url}/deals?token={config.TOKEN_RD}&page={page}&limit={limit}"
            if win is not None:
                win_param = str(win).lower() if isinstance(win, bool) else win
                url += f"&win={win_param}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                dados.extend(data.get('deals', []))
                
                # Verifica se há mais páginas para buscar
                offset = data.get('has_more', False)
                page += 1
            else:
                break

        # Retorna os dados exportados
        return dados
    except Exception as e:
        print(f"Ocorreu um erro ao exportar negociações: {e}")
        return None

def reconciliar_campos_rd(documento_atual: Dict, deal_rd: Dict) -> Optional[Dict]:
    """Compara um documento de `warmup_projetos` com o deal correspondente
    no RD Station e retorna um dict pronto para `$set` (chaves em
    dot-notation), restrito à allowlist de campos que o RD Station é dono:
    `capa_projeto.codigo`, `capa_projeto.nome_vendedor`,
    `capa_projeto.email_vendedor`, `cliente.nome`, `cliente.cliente_id`,
    `formacao_preco.valor`, `rd_closed_at`.

    Não faz nenhum I/O - quem chama decide onde buscar o documento e o
    deal, e como aplicar o `$set`. Retorna `None` quando nenhum campo da
    allowlist diverge (evita um `update_one` sem necessidade). Nenhum campo
    fora dessa allowlist (ex.: `gerente_projeto`, `socio_responsavel`,
    `centro_resultado`, anexos) é considerado - são preenchidos/editados no
    SIC e nunca devem ser sobrescritos por esta função.
    """
    documento_atual = documento_atual or {}
    deal_rd = deal_rd or {}
    organization = deal_rd.get("organization") or {}
    user = deal_rd.get("user") or {}

    valores_rd = {
        "capa_projeto.codigo": deal_rd.get("name", ""),
        "capa_projeto.nome_vendedor": user.get("name"),
        "capa_projeto.email_vendedor": user.get("email"),
        "cliente.nome": organization.get("name", ""),
        "cliente.cliente_id": organization.get("id", ""),
        "formacao_preco.valor": deal_rd.get("amount_total", 0),
        "rd_closed_at": deal_rd.get("closed_at"),
    }

    def _valor_atual(caminho):
        valor = documento_atual
        for parte in caminho.split("."):
            if not isinstance(valor, dict):
                return None
            valor = valor.get(parte)
        return valor

    divergentes = {
        caminho: novo_valor
        for caminho, novo_valor in valores_rd.items()
        if _valor_atual(caminho) != novo_valor
    }

    return divergentes or None


def export_deals_proposta_comercial():
    """
    Exporta os dados das negociações do CRM e retorna os dados serializados.
    """
    deal_stage_id = '66269b3cf210e6000f033c13'
    closed_at = False
    base_url = "https://crm.rdstation.com/api/v1"
    headers = {"accept": "application/json"}
    page = 1
    limit = 200
    offset = True
    dados = []
    

    try:
        while offset:
            url = f"{base_url}/deals?token={config.TOKEN_RD}&page={page}&limit={limit}&closed_at={closed_at}&deal_stage_id={deal_stage_id}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                dados.extend(data.get('deals', []))
                
                # Verifica se há mais páginas para buscar
                offset = data.get('has_more', False)
                page += 1
            else:
                break

        # Retorna os dados exportados
        return dados
    except Exception as e:
        print(f"Ocorreu um erro ao exportar negociações: {e}")
        return None
