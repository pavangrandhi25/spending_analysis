import boto3
import json
from logger import logger

class Rds_db:
    def get_secret(self,secret_name):
        try:
            session = boto3.session.Session()
            client = session.client(service_name='secretsmanager', region_name='us-east-1')
            response = client.get_secret_value(SecretId=secret_name)
        
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
            else:
                decoded_binary_secret = base64.b64decode(response['SecretBinary'])
                secret = decoded_binary_secret

            return secret
        except Exception as e:
            logger.error(f"Error in get_secret from rds db: {e}")
            return None

    def get_db_details(self):
        try:
            cred={}
            rds = boto3.client('rds')
            instances = rds.describe_db_instances()
            for instance in instances['DBInstances']:
                cred['endpoint'] = instance['Endpoint']['Address'] 
                cred['port'] = str(instance['Endpoint']['Port'])
                cred['secret_name'] = instance['MasterUserSecret']['SecretArn']
            
            secret_name='-'.join(cred['secret_name'].split(':')[-1].split('-')[:-1])
            db_secret_name = self.get_secret(secret_name)
            cred['username'] = db_secret_name['username']
            cred['password'] = db_secret_name['password']
            return cred
        except Exception as e:
            logger.error(f"Error in get_db_details from rds db: {e}")
            return None
