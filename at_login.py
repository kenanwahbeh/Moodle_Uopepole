import requests
from dotenv import load_dotenv
import os
import json
load_dotenv()


token = os.getenv("TEST_TOKEN")

# 🔐 ضع التوكن هنا مباشرة أو استورده من قاعدة البيانات

endpoint = "https://my.uopeople.edu/webservice/rest/server.php"

params = {
    "wstoken": token,
    "wsfunction": "core_webservice_get_site_info",
    "moodlewsrestformat": "json"
}

response = requests.get(endpoint, params=params)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))  # ← طباعة جميلة للبيانات
else:
    print("❌ فشل الاتصال")