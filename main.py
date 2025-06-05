import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from db_manager import DBManager

load_dotenv()

# إعدادات
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
login_url = os.getenv("LOGIN_URL")
data_url = os.getenv("DATA_URL")
secret_key = os.getenv("SECRET_KEY")

# قاعدة البيانات
db = DBManager(data_url, secret_key)
user_id = db.get_user_id(username, password)


def login():
    session = requests.Session()
    response = session.get(login_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        logintoken_input = soup.find('input', {'name': 'logintoken'})
        if logintoken_input:
            logintoken = logintoken_input['value']
            payload = {
                'anchor': '',
                'logintoken': logintoken,
                'username': username,
                'password': password
            }
            post_response = session.post(login_url, data=payload)
            if post_response.status_code == 200:
                print("✅ تم تسجيل الدخول بنجاح.")
                db.save_session(user_id, session)
                return session
    print("❌ فشل تسجيل الدخول.")
    return None


def get_authenticated_session():
    session = db.load_session(username)
    if session:
        test = session.get("https://my.uopeople.edu/my/")
        if "login" not in test.url:
            print("✅ الجلسة لا تزال صالحة.")
            return session
        else:
            print("⚠️ الجلسة منتهية. تسجيل دخول جديد.")
            return login()
    print("⚠️ لا توجد جلسة محفوظة. تسجيل دخول جديد.")
    return login()


def extract_and_store_token(session):
    url = "https://my.uopeople.edu/user/managetoken.php"
    resp = session.get(url)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tbody tr')
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2 and "Moodle mobile web service" in cells[1].text:
                token = cells[0].text.strip()
                db.save_token(user_id, token)
                print(f"✅ تم حفظ التوكين بنجاح: {token[:5]}***")
                return token
    print("❌ لم يتم العثور على التوكين المطلوب.")
    return None


def is_token_valid(token):
    try:
        response = requests.get(
            "https://my.uopeople.edu/webservice/rest/server.php",
            params={
                "wstoken": token,
                "wsfunction": "core_webservice_get_site_info",
                "moodlewsrestformat": "json"
            }
        )
        return response.status_code == 200 and "exception" not in response.text
    except Exception as e:
        print(f"⚠️ تحقق التوكين فشل: {e}")
        return False


# ✅ بدء التنفيذ
token = db.get_decrypted_token(username)

if token and is_token_valid(token):
    print(f"✅ التوكين صالح: {token[:5]}***")
else:
    print("⚠️ لا يوجد توكين أو التوكين غير صالح. سنحاول تسجيل الدخول.")
    session = get_authenticated_session()
    if session:
        extract_and_store_token(session)
    else:
        print("❌ فشل في الحصول على جلسة نشطة.")
    