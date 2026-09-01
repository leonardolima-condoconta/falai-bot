import urllib.request, re, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Get login page
req = urllib.request.Request('https://condoconta.inhire.app/login', 
    headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')

# Find __NEXT_DATA__
m = re.search(r'__NEXT_DATA__\s*=\s*({.*?});', resp, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print("NEXT_DATA buildId:", data.get('buildId'))
    print("Props keys:", list(data.get('props', {}).keys()))
else:
    print("No __NEXT_DATA__ found")
    print("Page length:", len(resp))
    print("First 2000 chars:", resp[:2000])