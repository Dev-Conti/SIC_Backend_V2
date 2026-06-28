from app.config import Config
from app.extensions import mongo
from app.blueprints.psoffice.services import PsofficeServices
import requests

psoffice_services = PsofficeServices()

class DeskManagerServices:
    def __init__(self):
        self.api_url = Config.DESK_API_URL
        self.chave_operador = Config.DESK_OPERADOR_KEY
        self.chave_publica = Config.DESK_PUBLIC_KEY
        self.token = self.authenticate()

    def authenticate(self):
        url = f"{self.api_url}/Login/autenticar"
        headers = {"Authorization": self.chave_operador}
        data = {"PublicKey": self.chave_publica}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def obter_dados_api(self, endpoint, payload=None):
        url = f"{self.api_url}/{endpoint}/lista"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload) if payload else requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json().get('root', [])

    def obter_clientes(self):
        return self.obter_dados_api("Clientes")

    def obter_contratos(self):
        contratos = self.obter_dados_api("Contratos")
        projetos_ams = psoffice_services.get_projetos_ams()

        for contrato in contratos:
            for projeto in projetos_ams:
                if contrato["Nome"] == projeto["codigo"]:
                    contrato["projId"] = projeto["projId"]
                    contrato["crId"] = projeto["crId"]
                    break

        return contratos

    def obter_chamados_suporte(self):
        return self.obter_dados_api("ChamadosSuporte")

    def obter_usuarios(self):
        return self.obter_dados_api("Usuarios")

    def obter_chamado_historicos(self):
        payload = {"Solicitante": "N"}
        return self.obter_dados_api("ChamadoHistoricos", payload)

    def obter_pesquisa_satisfacao(self):
        payload = {"ModoExibicao": "Alternativa"}
        return self.obter_dados_api("PesquisaSatisfacao", payload)

