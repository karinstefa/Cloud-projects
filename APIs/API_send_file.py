from flask import Flask
from flask import request
import boto3
import os
app = Flask(__name__)

from dotenv import load_dotenv
load_dotenv()

bucket_name = os.getenv('BUCKET_NAME')
queueName = os.getenv('QUEUE_NAME')

@app.route('/users', methods=['POST'])
def user():
    if request.method == 'POST':
        data = request.get_json()
        file_name = data['file_name']
        file_path = data['file_path']
        id_voz = data['id_voz']
        correo = data['correo']
        
        # Create SQS client
        sqs = boto3.client('sqs', region_name='us-east-1')
        # %%
        queue_url = f'https://sqs.us-east-1.amazonaws.com/734030550837/{queueName}'
        # %%
        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageAttributes={
                'FileName': {
                    'DataType': 'String',
                    'StringValue': file_name
                },
                'FilePath': {
                    'DataType': 'String',
                    'StringValue': file_path
                },
                'correo': { 
                    'DataType': 'String',
                    'StringValue': correo
                },
                'Id_voz': {
                    'DataType': 'String',
                    'StringValue': str(id_voz)
                }
            },
            MessageDeduplicationId='string',
            MessageGroupId="11",
            MessageBody=(
                'Documento up id_voz: ' + str(id_voz)
            )
        )

        return ({
                'success' : True,
                'message' : 'Archivo enviado correctamente',
                'id_voz' : id_voz
            })

    else:
        print('POST Error 405 Method Not Allowed')
        return ({'Sucess': 'False'})
