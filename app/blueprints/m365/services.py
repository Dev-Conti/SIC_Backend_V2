import requests
import base64
from app.config import Config

class M365AppToken:
    def __init__(self):
        self.client_id = Config.MSAL_CLIENT_ID
        self.client_secret = Config.MSAL_CLIENT_SECRET
        self.tenant_id = Config.MSAL_TENANT_ID
        self.token_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'

    def get_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']

class M365Services:
    def __init__(self, access_token):
        self.base_url = 'https://graph.microsoft.com/v1.0'
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

    def get_user_profile(self):
        profile_url = f'{self.base_url}/me'
        profile_response = requests.get(profile_url, headers=self.headers)
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            profile_data['photo'] = self.get_user_photo()
            return profile_data
        else:
            profile_response.raise_for_status()

    def get_user_photo(self):
        photo_url = f'{self.base_url}/me/photo/$value'
        photo_response = requests.get(photo_url, headers=self.headers)
        
        if photo_response.status_code == 200:
            return base64.b64encode(photo_response.content).decode('utf-8')
        elif photo_response.status_code == 404:
            # User does not have a photo
            return ''
        else:
            photo_response.raise_for_status()

    def get_complete_user_profile(self):
        profile_data = self.get_user_profile()
        profile_data['photo'] = self.get_user_photo()
        return profile_data
    
    def get_all_groups(self):
        groups_url = f'{self.base_url}/groups'
        all_groups = []

        while groups_url:
            groups_response = requests.get(groups_url, headers=self.headers)
            
            if groups_response.status_code == 200:
                groups_data = groups_response.json()
                all_groups.extend(groups_data.get('value', []))
                groups_url = groups_data.get('@odata.nextLink')
            else:
                groups_response.raise_for_status()

        filtered_groups = []
        for group in all_groups:
            filtered_groups.append({
                'displayName': group.get('displayName'),
                'id': group.get('id'),
                'email': group.get('mail'),
                'visibility': group.get('visibility')
            })
        return filtered_groups

    def get_group_channels(self, group_id):
        channels_url = f'{self.base_url}/teams/{group_id}/channels'
    
        channels_response = requests.get(channels_url, headers=self.headers)
        
        if channels_response.status_code == 200:
            channels_data = channels_response.json().get('value', [])
            filtered_channels = []
            for channel in channels_data:
                filtered_channels.append({
                    'displayName': channel.get('displayName'),
                    'tenantId': channel.get('tenantId'),
                    'id': channel.get('id'),
                    'membershipType': channel.get('membershipType')
                })
            return filtered_channels
        else:
            channels_response.raise_for_status()

    def get_channel_members(self, group_id, channel_id):
        """
        Obtém os membros de um canal específico dentro de uma equipe e identifica se são owners.

        Args:
            group_id (str): ID da equipe do Microsoft Teams.
            channel_id (str): ID do canal dentro da equipe.

        Returns:
            list: Lista de membros com suas informações e indicação se são owners.
        """
        try:
            # Endpoint da Graph API para membros do canal
            endpoint = f"https://graph.microsoft.com/v1.0/teams/{group_id}/channels/{channel_id}/members"
            headers = self.headers

            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()  # Lança uma exceção se o status não for 200

            # Processa a resposta JSON
            members_data = response.json().get("value", [])
            
            # Monta a lista de membros com a verificação de owner
            members_with_roles = []
            for member in members_data:
                members_with_roles.append({
                    "id": member["userId"],
                    "displayName": member.get("displayName", "Desconhecido"),
                    "email": member.get("email", member.get("userPrincipalName")),
                    "isOwner": "owner" in member.get("roles", [])
                })

            return members_with_roles

        except requests.RequestException as e:
            raise Exception(f"Erro ao obter membros do canal: {e}")
