# %% imports
from fileinput import filename
import boto3

# %% Variables
sqs = boto3.client('sqs',region_name='us-east-1')
s3 = boto3.client('s3')

bucket_name = 'test-bucket-cloud-1'
queueName = 'test.fifo'
folder = 'test'
filename = ''
# %% 1 Leer SQS
queue_url = f'https://sqs.us-east-1.amazonaws.com/734030550837/{queueName}'

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    MessageAttributeNames=[
        'All'
    ]
)
message = response['Messages'][0]
receipt_handle = message['ReceiptHandle']
# %% 2 dynamodb check estado
# % 3 dynamodb update estado enProceso

# %% 4 bajar archivo de S3
# % 5 convertir a mp3 local
cmd = f" ffmpeg -i {url_up} -af aresample=async=1:first_pts=0 {filename}.mp3"

# %% 6 subir archivo a S3
file_name_with_extention = f'{folder}/{filename}.mp3'

s3.put_object(  Body=msg, 
                Bucket=bucket_name,
                Key=file_name_with_extention)

# %% 7 actualizar estado en bd
url_down = f'https://{bucket_name}.s3.amazonaws.com/{folder}/{filename}.mp3'

# %% 8 enviar correo

# %% 9 borrar mensaje de SQS
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle
)