import os
import smtplib
from sqlalchemy import create_engine

db_string = "postgresql://admin:123456@172.24.41.222:5432/project01"

db = create_engine(db_string)

gmail_user = 'p.cloud.u01@gmail.com'
gmail_password = 'milo te da energia'


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
                os.system(cmd)
            except Exception as e:
                print(e)
            path_convertido = f'{nombre}.mp3'
        else:
            path_convertido = patho

        # enviar correo
        try:
            server = smtplib.SMTP('smtp.gmail.com', 25)
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_password)
            print("Loged ok")
            # message to be sent   
            SUBJECT = "Estado concurso"   
            TEXT = "En hora buena hemos convertido tu voz, esta ya ha sido publicada en la pagina publica del concurso. Muchos exitos!!!"
            
            message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)

            # to = 'p.cloud.u01@gmail.com'
            # header = 'To:' + to + '\n' + 'From:' + gmail_user + '\n' + 'Estado concurso \n'
            
            # msg = header + '\n En hora buena hemos convertido tu voz, esta ya ha sido publicada en la pagina publica del concurso. Muchos exitos!!!'
            
            server.sendmail(gmail_user, correo, message)   
            print("send email ok")    
            db.execute(f"UPDATE Voces SET Estado = 1, path_convertido='{path_convertido}' WHERE id = {r['id']}")
        except Exception as e:
            print(e)


    """
    path = f'{sys.path[0]}/voces'
    files = [f for f in listdir(path) if isfile(join(path, f))]
    # leer bd para saber cuales faltan por convertir
    for file in files:
        [nombre, ext] = file.split('.')
        if ext != 'mp3':
            cmd = f'{sys.path[0]}/ffmpeg.exe -i {path}/{nombre}.{ext} {path}/mp3/{nombre}.mp3'
            #os.system(cmd)
            # cambiar estado en bd
            # enviar correo
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, correo, " ""\
                    Subject: Tu voz se ha convertido!
                    En hora buena hemos convertido tu voz, esta ya ha sido publicada en la 
                    página pública del concurso. Muchos exitos!!!" "")         
            except:
                print('Something went wrong...')
                """