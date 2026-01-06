import hmac
import hashlib
import base64

def genSha256(key,message):
    key=key.encode('utf-8')
    message=message.encode('utf-8')


    hmac_sha256 = hmac.new(key, message, hashlib.sha256)
    digest = hmac_sha256.digest()
    signature = base64.b64encode(digest).decode('utf-8') 

    return signature