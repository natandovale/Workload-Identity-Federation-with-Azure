from google.cloud import storage 
from google.oauth2.sts import Client 
import google.oauth2. credentials 
import google.auth.transport.requests 
from google.cloud. iam_credentials import IAMCredentialsClient 
from azure. identity import ClientSecretCredential

class AzureGoogleAccountInfo:

 def __init__(self, 
              azure_tenant_id: str,
              azure_client_id: str,
              azure_client_secret: str,
              google_audience: str,
              google_service_account_email: str):
     self.azure_tenant_id = azure_tenant_id
     self.azure_client_id = azure_client_id
     self.azure_client_secret = azure_client_secret
     self.google_audience = google_audience
     self.google_service_account_email = google_service_account_email

class AzureGoogleToken:
   _SCOPE = "https://www.googleapis.com/auth/cloud-platform"
   _AZURE_SCOPE = "https://management.core.windows.net/.default"
   _GOOGLE_STS_ADDRESS = "https://sts.googleapis.com/v1/token"
   _GOOGLE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type: token-exchange"
   _GOOGLE_SUBJECT_TOKEN_TYPE= "urn:ietf:params: oauth: token-type: jwt"
   _GOOGLE_REQUESTED_TOKEN_TYPE = "urn:ietf:params:oauth: token-type: access_token"

   def __init__(self, account_info: AzureGoogleAccountInfo):
       self._azure_info = account_info

   def _get_azure_token(self) -> str:
       azure_client = ClientSecretCredential(self._azure_info.azure_tenant_id,
                                             self._azure_info.azure_client_id,
                                             self._azure_info.azure_client_secret)
       return azure_client.get_token(self._AZURE_SCOPE). token

   def _get_sts_token (self) -> dict:
       subject_token = self._get_azure_token()
       request = google.auth.transport.requests. Request()
       sts_client = Client (self._GOOGLE_STS_ADDRESS)
       return sts_client.exchange_token (request=request,
                                         grant_type=self._GOOGLE_GRANT_TYPE,
                                         subject_token=subject_token,
                                         subject_token_type=self._GOOGLE_SUBJECT_TOKEN_TYPE,
                                         requested_token_type=self._GOOGLE_REQUESTED_TOKEN_TYPE,
                                         scopes=["https://www.googleapis.com/auth/cloud-platform"],
                                         audience=self._azure_info.google_audience
                                         )

   def _get_impersonated_token(self) -> str:
       sts_token= self._get_sts_token()
       credentials = google.oauth2.credentials.Credentials (sts_token ['access_token'])
       iam = IAMCredentialsClient (credentials=credentials)
       return iam.generate_access_token(
           name=f"projects/-/serviceAccounts/{self._azure_info.google_service_account_email}",
           scope=["https://www.googleapis.com/auth/cloud-platform"]).access_token

   def _generate_google_credentials_from_token (self)->google.oauth2.credentials.Credentials:
       self._service_account_token = self._get_impersonated_token()
       self._google_credentials = google.oauth2.credentials. Credentials(self._service_account_token)
       return self._google_credentials

   def get_google_credentials (self):
       return self._generate_google_credentials_from_token()

TENANT_ID = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
PROJECT_NUMBER = ""
WORKLOAD_POOL = ""
WORKLOAD_POOL_PROVIDER = ""
SERVICE_ACCOUNT_EMAIL = ""
GOOGLE_AUDIENCE = f"//iam.googleapis.com/projects/{PROJECT_NUMBER}/locations/" \
                  f"global/workloadIdentityPools/{WORKLOAD_POOL}/providers/{WORKLOAD_POOL_PROVIDER}"

account_info = AzureGoogleAccountInfo(azure_tenant_id=TENANT_ID,
                                      azure_client_id=CLIENT_ID,
                                      azure_client_secret=CLIENT_SECRET,
                                      google_audience=GOOGLE_AUDIENCE,
                                      google_service_account_email=SERVICE_ACCOUNT_EMAIL
                                      )

azure_google_token = AzureGoogleToken (account_info)
credentials = azure_google_token.get_google_credentials ()

client = storage. Client (credentials=credentials, project='Project Id')

bucket = storage. Bucket (client, 'Bucket Name', 'Project Id')

buckets = list(client.list_blobs (bucket))

for bucket in buckets:
    print (bucket)