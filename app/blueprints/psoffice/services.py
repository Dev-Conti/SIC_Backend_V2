from app.config import Config
from app.extensions import mongo,db_psoffice
import requests
from datetime import datetime, timedelta
from app.utils.file_utils import load_file

class PsofficeServices_old:
    def __init__(self):
        self.api_url = Config.PSOFFICE_API_URL
        self.token = Config.TOKEN_PSOFFICE

    def get_centros_resultado(self):
        url = f"{self.api_url}/api/v1/centrosresultado/centrosresultado"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def get_pessoas_juridicas(self):
        url = f"{self.api_url}/api/v1/pessoasjuridicas/pessoasjuridicas"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def get_projetos(self):
        url = f"{self.api_url}/api/rest/projeto"
        headers = {"Authorization": f"Bearer {self.token}"}
        all_projects = []
        index = 0
        size = 100

        while True:
            response = requests.get(url, headers=headers, params={"index": index, "size": size})
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            all_projects.extend(data["info"]["itens"])
            if not data["info"]["next"]:
                break
            index += size

        return all_projects
    
    def get_cr_ams(self):
        return [24, 25, 26, 9]

    def get_projetos_ams(self, status_projeto="Liberado"):
        centros_resultado = self.get_centros_resultado()
        projetos = self.get_projetos()

        cr_ams = self.get_cr_ams()
        filtered_centros = [cr for cr in centros_resultado if int(cr["CR_ID"]) in cr_ams]
        filtered_projetos = [
            projeto for projeto in projetos 
            if int(projeto["crId"]) in cr_ams and projeto["wkfStepDesc"] == status_projeto
        ]

        print(f"Quantidade de projetos: {len(filtered_projetos)}")
        
        return filtered_projetos
    
    def get_projetos_v2(self):
        query = """
            SELECT 
                proj_id, 
                emp_id, 
                cli_id,
                cr_id, 
                codigo, 
                usu_emp_id, 
                tipo_de_projeto, 
                wkf_step_desc,
                valor 
            FROM 
                pso_projetos;
            """
        db_psoffice.connect()
        try:
            results, headers = db_psoffice.execute_query(query)
            projetos = [dict(zip(headers, row)) for row in results]
        finally:
            db_psoffice.close()
        
        return projetos

    def get_apontamentos_v2(self, data_inicio, data_fim):        
        # Garantir que as datas estejam no formato YYYY-MM-DD
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%Y-%m-%d')

        except ValueError:
            raise ValueError("Formato de data inválido. Use o formato yyyy-mm-dd.")
        
        # Carregar a query SQL do arquivo
        query = load_file("get_apontamentos.sql", folder="queries/sql_server")
        
        # Substituir os parâmetros na query
        query = query.replace(":data_inicio", f"'{data_inicio}'").replace(":data_fim", f"'{data_fim}'")
        
        # Conectar ao banco de dados e executar a query
        db_psoffice.connect()
        results, headers = db_psoffice.execute_query(query)
        db_psoffice.close()
        
        # Transformar os resultados em uma lista de dicionários
        apontamentos = [dict(zip(headers, row)) for row in results]
        
        return apontamentos

class PsofficeServices:
    def __init__(self):
        self.api_url = Config.PSOFFICE_API_URL
        self.token = Config.TOKEN_PSOFFICE

    def buscar_usuarios(self):        
        # Carregar a query SQL do arquivo
        query = load_file("get_usuarios_psoffice.sql", folder="queries/sql_server")
                
        # Conectar ao banco de dados e executar a query
        db_psoffice.connect()
        results, headers = db_psoffice.execute_query(query)
        db_psoffice.close()
        
        # Transformar os resultados em uma lista de dicionários
        data = [dict(zip(headers, row)) for row in results]
        
        return data

    def buscar_centros_resultado(self):
        url = f"{self.api_url}/api/v1/centrosresultado/centrosresultado"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def buscar_pessoas_juridicas(self):
        url = f"{self.api_url}/api/v1/pessoasjuridicas/pessoasjuridicas"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def buscar_projetos(self):        
        # Carregar a query SQL do arquivo
        query = load_file("get_projetos_psoffice.sql", folder="queries/sql_server")
        
        # Conectar ao banco de dados e executar a query
        db_psoffice.connect()
        results, headers = db_psoffice.execute_query(query)
        db_psoffice.close()
        
        # Transformar os resultados em uma lista de dicionários
        data = [dict(zip(headers, row)) for row in results]
        
        return data

    def buscar_cr_ams(self):
        return [24, 25, 26, 9]

    def buscar_projetos_ams(self, status_projeto="Liberado"):
        centros_resultado = self.get_centros_resultado()
        projetos = self.get_projetos()

        cr_ams = self.get_cr_ams()
        filtered_centros = [cr for cr in centros_resultado if int(cr["CR_ID"]) in cr_ams]
        filtered_projetos = [
            projeto for projeto in projetos 
            if int(projeto["crId"]) in cr_ams and projeto["wkfStepDesc"] == status_projeto
        ]

        print(f"Quantidade de projetos: {len(filtered_projetos)}")
        
        return filtered_projetos
    
    def buscar_projetos_v2(self):
        query = """
            SELECT 
                proj_id, 
                emp_id, 
                cli_id,
                cr_id, 
                codigo, 
                usu_emp_id, 
                tipo_de_projeto, 
                wkf_step_desc,
                valor 
            FROM 
                pso_projetos;
            """
        db_psoffice.connect()
        try:
            results, headers = db_psoffice.execute_query(query)
            projetos = [dict(zip(headers, row)) for row in results]
        finally:
            db_psoffice.close()
        
        return projetos

    def buscar_apontamentos_v2(self, data_inicio, data_fim):        
        # Garantir que as datas estejam no formato YYYY-MM-DD
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%Y-%m-%d')

        except ValueError:
            raise ValueError("Formato de data inválido. Use o formato yyyy-mm-dd.")
        
        # Carregar a query SQL do arquivo
        query = load_file("get_apontamentos_psoffice.sql", folder="queries/sql_server")
        
        # Substituir os parâmetros na query
        query = query.replace(":data_inicio", f"'{data_inicio}'").replace(":data_fim", f"'{data_fim}'")
        
        # Conectar ao banco de dados e executar a query
        db_psoffice.connect()
        results, headers = db_psoffice.execute_query(query)
        db_psoffice.close()
        
        # Transformar os resultados em uma lista de dicionários
        apontamentos = [dict(zip(headers, row)) for row in results]
        
        return apontamentos

