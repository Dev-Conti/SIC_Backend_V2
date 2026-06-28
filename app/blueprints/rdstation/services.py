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
                    url += f"&win={win}"
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
                url += f"&win={win}"
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
