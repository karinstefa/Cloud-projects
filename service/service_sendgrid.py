import json
import requests
url_sendgrid = 'https://api.sendgrid.com/v3/mail/send'
SENDGRID_API_KEY= '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'
paramail = 'karinstefa@gmail.com'
asunto = "Hello, World!"
mensaje = 'texto'

data_to_send ={
    "personalizations": [
        {
            "to": [
                {
                    "email": paramail
                }
            ]
        }
    ],
    "from": {
        "email": "p.cloud.u01@gmail.com"
    },
    "subject": asunto,
    "content": [
        {
            "type": "text/plain",
            "value": mensaje
        }
    ]
}
myheader = {
      "Authorization": f'Bearer {SENDGRID_API_KEY}',
      'Content-Type': 'application/json'}
print(myheader)

result = requests.post(url=url_sendgrid,
 data =json.dumps( data_to_send),
  headers = myheader)

print(result.text)
