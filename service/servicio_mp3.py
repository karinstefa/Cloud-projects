import os.path
from sqlalchemy import create_engine

import json
import requests

url_sendgrid = 'https://api.sendgrid.com/v3/mail/send'

SENDGRID_API_KEY = ''
mensaje = 'texto'

db_string = "postgresql://postgres:cloud1234@database-2.cnjddgnl0ynw.us-east-1.rds.amazonaws.com:5432/db_concursos"

db = create_engine(db_string)

result_set = db.execute("SELECT * FROM Voces WHERE Estado =0")
for r in result_set:
    correo = r['correo']
    patho = r['path_original']
    if patho != None:
        [nombre, ext] = patho.split('.')
        if ext != 'mp3':
            cmd = f'ffmpeg -i {patho} {nombre}.mp3'

            print(cmd)
            try:
                if (os.path.exists(patho)):
                    os.system(cmd)
            except Exception as e:
                print('Error conversion:')
                print(e)
            path_convertido = f'{nombre}.mp3'
        else:
            path_convertido = patho

        # enviar correo
        try:

            data_to_send = {
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
                    "email": "cloud.uniaandes@gmail.com"
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
                "Authorization": f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'}

            result = requests.post(url=url_sendgrid, data=json.dumps(data_to_send), headers=myheader)


            db.execute(f"UPDATE Voces SET Estado = 1, path_convertido='{path_convertido}' WHERE id = {r['id']}")
        except Exception as e:
            print('Error envio:')
            print(e)