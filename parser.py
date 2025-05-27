import requests
import json
import re
import html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def login_est_lv(username, password):
    session = requests.Session()

    login_url = "https://www.e-st.lv/lv/private/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "lv-LV,lv;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.e-st.lv/"
    }

    resp = session.get(login_url, headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch login page: {e}")
        print("Response content snippet:", resp.text[:500])
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input:
        print("CSRF token '_token' not found")
        return None
    csrf_token = token_input['value']

    payload = {
        "_token": csrf_token,
        "login": username,
        "password": password,
        "returnUrl": login_url
    }

    resp = session.post(login_url, data=payload, headers=headers, allow_redirects=True)
    if resp.status_code != 200:
        print(f"Login POST failed with status: {resp.status_code}")
        return None

    if "PROD_ST_SESSION" in session.cookies.get_dict():
        print("[✓] Logged in successfully.")
        return session
    else:
        print("[✗] Login failed.")
        return None

def fetch_graph_page(session, object_eic, counter_number):
    url = f"https://mans.e-st.lv/lv/private/paterini-un-norekini/paterinu-grafiki/?objectEic={object_eic}&counterNumber={counter_number}&period=D"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.e-st.lv/lv/private/"
    }

    resp = session.get(url, headers=headers)
    if resp.status_code == 200:
        print("[✓] Graph page fetched successfully.")
        return resp.text  # Return the HTML content
    else:
        print(f"[✗] Failed to fetch graph page (HTTP {resp.status_code})")
        return None

def extract_hourly_consumption_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    chart_div = soup.find("div", class_="chart")
    if not chart_div or not chart_div.has_attr("data-values"):
        print("[✗] Chart data not found.")
        return None

    # Unescape HTML entities and parse JSON
    data_values = html.unescape(chart_div["data-values"])
    data = json.loads(data_values)

    # Extract hourly A+ consumption (imported energy)
    try:
        hourly_data = data["values"]["A+"]["DAY_NIGHT"]["data"]
        result = []
        for entry in hourly_data:
            dt = datetime.utcfromtimestamp(entry["timestamp"] / 1000)
            result.append({
                "datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "value": entry["value"]
            })
        return result
    except Exception as e:
        print("[✗] Failed to extract hourly data:", e)
        return None

if __name__ == "__main__":
    # ⚠️ Replace these with your real credentials (or load from env vars)
    username = "username"
    password = "password"

    object_eic = "xxx-STOxxxxxxxxH"
    counter_number = "xxxxxxxx"

    session = login_est_lv(username, password)
    # print("Session cookies:", session.cookies.get_dict())
    fetch_graph_page(session, object_eic, counter_number)
    html_content = fetch_graph_page(session, object_eic, counter_number)

    hourly = extract_hourly_consumption_from_html(html_content)
    if hourly:
        for h in hourly:
            print(h)

    total = sum(entry["value"] for entry in hourly)
    print(round(total, 3))
