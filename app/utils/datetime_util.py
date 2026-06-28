from datetime import datetime, timedelta
import pytz
from zoneinfo import ZoneInfo
import requests

class DatetimeServices:
    @staticmethod
    def data_hoje():
        return datetime.today().strftime("%Y-%m-%d")
    @staticmethod
    def data_anterior_ndias(days=30, data_str=None):
        if data_str is None:
            data = datetime.today()  # Usa a data atual se `data_str` não for passado
        else:
            data = datetime.strptime(data_str, "%Y-%m-%d")
        
        nova_data = data - timedelta(days=days)
        return nova_data.strftime("%Y-%m-%d")

    
    @staticmethod
    def obter_anos(data_inicio: str, data_fim: str):
        ano_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').year
        ano_fim = datetime.strptime(data_fim, '%Y-%m-%d').year

        if ano_inicio == ano_fim:
            return ano_inicio
        else:
            return list(range(ano_inicio, ano_fim + 1))

    @staticmethod
    def buscar_datas_feriados(years):
        """
        Busca os feriados de uma API com base na lista de anos fornecida ou um único ano.
        Retorna apenas os feriados onde o tipo é "Public" e counties é null.
        """
        if isinstance(years, int):
            years = [years]
        
        all_holidays = []
        for year in years:
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/BR"
            response = requests.get(url)
            if response.status_code == 200:
                holidays = response.json()
                public_holidays = [
                    holiday for holiday in holidays 
                    if "Public" in holiday["types"] and holiday["counties"] is None
                ]
                all_holidays.extend(public_holidays)
            else:
                response.raise_for_status()
        all_holidays = [datetime.strptime(holiday["date"], "%Y-%m-%d").date() for holiday in all_holidays]
        return all_holidays
    
    @staticmethod
    def calcular_diferenca_dias_uteis(data_inicio: str, data_fim: str, feriados: list = None) -> int:
        """
        Calcula a diferença de dias úteis entre duas datas no formato 'YYYY-MM-DD'.
        
        :param data_inicio: Data de início no formato 'YYYY-MM-DD'.
        :param data_fim: Data de término no formato 'YYYY-MM-DD'.
        :param feriados: Lista opcional de datas datetime de feriados.
        :return: Diferença de dias úteis entre as duas datas.
        """
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        if data_inicio > data_fim:
            data_inicio, data_fim = data_fim, data_inicio
        
        total_days = (data_fim - data_inicio).days + 1
        business_days = 0
        
        for day in range(total_days):
            current_day = data_inicio + timedelta(days=day)
            if current_day.weekday() < 5 and (feriados is None or current_day not in feriados):  # Monday to Friday are considered business days
                business_days += 1
        
        return business_days

    @staticmethod
    def converter_data_mongo(data_vencimento: str) -> str:
        """
        Converte uma string de data no formato '2025-01-01T00:00:00-03:00' para o formato 'YYYY-MM-DD'.
        
        :param data_vencimento: Data no formato '2025-01-01T00:00:00-03:00'.
        :return: Data no formato 'YYYY-MM-DD'.
        """
        data = datetime.strptime(data_vencimento, '%Y-%m-%dT%H:%M:%S%z')
        return data.strftime('%Y-%m-%d')


# Função para armazenar a data no banco em UTC, ajustada para o fuso horário de São Paulo
def store_date_in_utc(date_string: str) -> datetime:
    # Converte a string para datetime, assumindo que é no início do dia (00:00:00)
    date_obj = datetime.strptime(date_string, '%Y-%m-%d')
    
    # Define o fuso horário de São Paulo
    sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
    
    # Localiza a data no fuso horário de São Paulo
    local_datetime = sao_paulo_tz.localize(date_obj, is_dst=None)
    
    # Converte a data localizada para UTC
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    # Retorna o datetime em UTC para armazenar no banco
    return utc_datetime

# Função para obter a data atual no formato desejado (com fuso horário)
def get_local_datetime(timezone: str = 'America/Sao_Paulo') -> str:
    fuso_horario = pytz.timezone(timezone)
    data_local = datetime.now(pytz.utc).astimezone(fuso_horario)
    return data_local.isoformat()

# Função para converter um datetime UTC para um fuso horário específico
def convert_utc_to_timezone(utc_datetime: datetime, timezone: str = 'America/Sao_Paulo') -> str:
    fuso_horario = pytz.timezone(timezone)
    datetime_com_fuso = utc_datetime.replace(tzinfo=pytz.utc).astimezone(fuso_horario)
    return datetime_com_fuso.isoformat()

# Função para converter uma string de data para datetime local com fuso horário America/Sao_Paulo
def convert_date_string_to_local_datetime(date_str: str, timezone_str: str = 'America/Sao_Paulo') -> datetime:
    """
    Converte uma string de data no formato 'YYYY-MM-DD' para um objeto datetime localizado.
    
    :param date_str: Data no formato 'YYYY-MM-DD'.
    :param timezone_str: Fuso horário para a conversão.
    :return: Objeto datetime localizado.
    """
    try:
        naive_datetime = datetime.strptime(date_str, '%Y-%m-%d')
        local_timezone = pytz.timezone(timezone_str)
        localized_datetime = local_timezone.localize(naive_datetime)
        return localized_datetime
    except ValueError:
        raise ValueError("Formato de data inválido. Use o formato 'YYYY-MM-DD'.")

# Função para calcular a diferença entre duas datas (em segundos, minutos, etc.)
def calculate_time_difference(start_datetime: datetime, end_datetime: datetime) -> dict:
    difference = end_datetime - start_datetime
    return {
        'days': difference.days,
        'seconds': difference.seconds,
        'microseconds': difference.microseconds
    }

# Função para formatação personalizada (sem milissegundos ou apenas com o que você precisa)
def format_datetime_custom(datetime_obj: datetime, timespec: str = 'seconds') -> str:
    return datetime_obj.isoformat(timespec=timespec)
