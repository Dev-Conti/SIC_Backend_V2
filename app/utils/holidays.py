import requests

def fetch_holidays(years):
    """
    Busca os feriados de uma API com base na lista de anos fornecida.
    Retorna apenas os feriados onde o tipo é "Public" e counties é null.
    """
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
    return all_holidays
