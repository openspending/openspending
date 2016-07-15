import json
import zlib
import base64

secrets = {}

for x in ['google.key', 'google.secret.key', 'private.pem', 'public.pem']:
   secrets[x] = open(x).read().strip()

prefix = 'OS_CONDUCTOR_SECRETS_'

encoded = json.dumps(secrets).encode('ascii')
encoded = zlib.compress(encoded)
encoded = base64.encodebytes(encoded)
encoded = encoded.replace(b'\n',b'')
chunk = (len(encoded)+4)//4
print(chunk)

i=0
while len(encoded)>0:
   var = '%s%i' % (prefix,i)
   print('%s="%s"' % (var, encoded[:chunk].decode('ascii')))
   encoded = encoded[chunk:]
   i+=1
