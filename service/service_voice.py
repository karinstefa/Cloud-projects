# %% imports
import base64
import json
import boto3
import os
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key
import requests

load_dotenv()
# %% Variables de entorno
bucket_name = os.getenv('BUCKET_NAME')
queueName = os.getenv('QUEUE_NAME')
region_name = os.getenv('REGION_NAME')
sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
sendgrid_url = os.getenv('SENDGRID_URL')
# %% Create SQS and S3 client
sqs = boto3.client('sqs',region_name='us-east-1')
s3 = boto3.client('s3')
s31 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb', region_name = region_name)


# %% 1 Leer SQS
queue_url = f'https://sqs.us-east-1.amazonaws.com/734030550837/{queueName}'

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    MessageAttributeNames=[
        'All'
    ]
)

if 'Messages' in response:
    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    attributes = message['MessageAttributes']
    try :
        file_name = attributes['FileName']['StringValue']
        file_path = attributes['FilePath']['StringValue']
        id_voz = attributes['Id_voz']['StringValue']
        correo = attributes['correo']['StringValue']
        # %% 2 dynamodb check estado
        # % 3 dynamodb update estado enProceso
        table = dynamodb.Table('voz')
        responseDB = table.query(
            KeyConditionExpression=Key('pk').eq('voz#voz') & Key('sk').eq(id_voz)
        )
        if responseDB['Items'][0]['info']['estado'] == '0':
            print('En proceso')
            # %% 4 bajar archivo de S3
            [name,ext] = file_name.split('.')
            id_proc = id_voz.replace('|','_')
            
            s31.Bucket(bucket_name).download_file(file_path,f'tmp/vz_{id_proc}.{ext}')
            # % 5 convertir a mp3 local
            cmd = f" ffmpeg -i tmp/vz_{id_proc}.{ext} -af aresample=async=1:first_pts=0 tmp/vz_{id_proc}.mp3"
            os.system(cmd)
            # %% 6 subir archivo a S3
            voz_64=''
            with open(f"tmp/vz_{id_proc}.mp3", "rb") as voz_file:
                voz_64 = base64.b64encode(voz_file.read())            
            msg = base64.b64decode(voz_64)
            s3.put_object(Key=f"files/voz/{name}.mp3", Bucket=bucket_name, Body=msg)
            # eliminar archivos temporales
            os.remove(f"tmp/vz_{id_proc}.{ext}")
            os.remove(f"tmp/vz_{id_proc}.mp3")
            # %% 8 enviar correo
            try:
                data_to_send ={
                    "personalizations": [
                        {
                            "to": [
                                {
                                    "email": correo
                                }
                            ]
                        }
                    ],
                    "from": {
                        "email": "cursocloud2022@gmail.com"
                    },
                    "subject": "Estado concurso",
                    "content": [
                        {
                            "type": "text/plain",
                            "value": "En hora buena hemos convertido tu voz, esta ya ha sido publicada en la pagina publica del concurso. Muchos exitos!!!"
                        }
                    ]
                }
                myheader = {
                    "Authorization": f'Bearer {sendgrid_api_key}',
                    'Content-Type': 'application/json'}
                result = requests.post(
                    url = sendgrid_url,
                    data =json.dumps(data_to_send),
                    headers = myheader)
                print(result)
                
                # %% 7 actualizar estado en bd
                row = responseDB['Items'][0]['info']
                row.update({'estado': '1'})
                table.update_item(
                    Key={'pk': 'voz#voz', 'sk': id_voz},
                    AttributeUpdates={
                        'info': {
                            "Action": "PUT",
                            'Value': row
                        }
                    }
                )
                
            except Exception as e:
                print('Error envio:')
                print(e)
        else:
            print('Ya esta procesado')
    except Exception as e:
        print(e)
    # %% 9 borrar mensaje de SQS
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )