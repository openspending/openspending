import json

secrets = {}

for x in ['google.key', 'google.secret.key', 'private.pem', 'public.pem']:
   secrets[x] = open(x).read().strip()

prefix = 'OS_CONDUCTOR_SECRETS_'

encoded = json.dumps(secrets).encode('zip').encode('base64').replace('\n','')
chunk = (len(encoded)+4)/4

i=0
while len(encoded)>0:
   var = '%s%i' % (prefix,i)
   print '%s="%s"' % (var, encoded[:chunk])
   encoded = encoded[chunk:]
   i+=1
