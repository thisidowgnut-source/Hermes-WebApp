import browser_cookie3
import json
import os
import shutil

print("Extracting Chrome cookies...")
try:
    cookie_path = r"C:\Users\megat\AppData\Local\Google\Chrome\User Data\Profile 9\Network\Cookies"
    cj = browser_cookie3.chrome(domain_name='facebook.com', cookie_file=cookie_path)
    
    cookies_list = []
    for c in cj:
        if 'facebook.com' in c.domain:
            cookies_list.append({
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'path': c.path,
                'secure': c.secure,
                'httpOnly': 'HTTPOnly' in c._rest.get('HTTPOnly', '') if hasattr(c, '_rest') else False
            })

    if not cookies_list:
        print("No Facebook cookies found in the default Chrome profile.")
        # Attempt to specify the profile specifically if possible, but browser_cookie3 tries to find the default
    else:
        with open('C:\\Users\\megat\\Hermes-WebApp\\scripts\\fb_cookies.json', 'w') as f:
            json.dump(cookies_list, f, indent=4)
        print(f"Successfully extracted {len(cookies_list)} Facebook cookies to fb_cookies.json")

except Exception as e:
    print(f"Error extracting cookies: {e}")
