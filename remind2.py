import os
import requests
from datetime import datetime

# ── 設定區 ──────────────────────────────────────────────
NOTION_TOKEN       = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID_2"]

LINE_TOKEN         = os.environ["LINE_TOKEN"]
LINE_GROUP_ID      = os.environ["LINE_GROUP_ID_2"]
LINE_USER_ID       = os.environ["LINE_USER_ID_2"]

ENGINEER_PAGE_ID   = "3bf43c87619c49a7a18efea0539e18fd"
STATUS_INCOMPLETE  = ["0-未開始", "1-進行中", "2-請款結束_尚未完工"]
# ────────────────────────────────────────────────────────


def get_current_month_str():
    return f"{datetime.now().month}月"


def fetch_maintenance_tasks():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    current_month = get_current_month_str()

    payload = {
        "filter": {
            "and": [
                {
                    "property": "工程師",
                    "relation": {"contains": ENGINEER_PAGE_ID}
                },
                {
                    "property": "交易別",
                    "multi_select": {"contains": "維護案"}
                },
                {
                    "or": [
                        {"property": "訂單狀態", "status": {"equals": s}}
                        for s in STATUS_INCOMPLETE
                    ]
                },
                {
                    "property": "[工程師]維護月份",
                    "multi_select": {"contains": current_month}
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    tasks = []
    for page in results:
        props = page.get("properties", {})

        # 案名（標題欄位）
        title_list = props.get("案名", {}).get("title", [])
        name = "".join(t.get("plain_text", "") for t in title_list).strip()

        # 客戶（related）- 查詢頁面名稱
        customers = props.get("客戶", {}).get("relation", [])
        customer_name = ""
        if customers:
            cid = customers[0]["id"]
            cr = requests.get(
                f"https://api.notion.com/v1/pages/{cid}",
                headers={
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Notion-Version": "2022-06-28"
                }
            )
            if cr.ok:
                cp = cr.json().get("properties", {})
                for v in cp.values():
                    if v.get("type") == "title":
                        tl = v.get("title", [])
                        customer_name = "".join(t.get("plain_text", "") for t in tl).strip()
                        break

        # 訂單起迄日
        start_date = props.get("訂單起日", {}).get("date") or {}
        end_date = props.get("訂單迄日", {}).get("date") or {}
        start = start_date.get("start", "")
        end = end_date.get("start", "")

        if name:
            tasks.append({
                "name": name,
                "customer": customer_name,
                "start": start,
                "end": end,
            })

    return tasks


def send_line_message(tasks):
    if not tasks:
        print("沒有符合條件的維護案，略過傳送。")
        return

    current_month = get_current_month_str()
    task_lines = ""
    for t in tasks:
        task_lines += f"• {t['customer']}｜{t['name']}\n"
        task_lines += f"  📅 {t['start']} ~ {t['end']}\n\n"

    payload = {
        "to": LINE_GROUP_ID,
        "messages": [
            {
                "type": "textV2",
                "text": f"🔧 {current_month}維護案提醒\n\n{{mention}}，本月需追蹤的維護案共 {len(tasks)} 件：\n\n{task_lines}請確認進度！",
                "substitution": {
                    "mention": {
                        "type": "mention",
                        "mentionee": {
                            "type": "user",
                            "userId": LINE_USER_ID,
                        }
                    }
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    print(f"✅ 已傳送提醒，共 {len(tasks)} 件維護案。")


if __name__ == "__main__":
    print("🔍 讀取 Notion 維護案清單...")
    tasks = fetch_maintenance_tasks()
    print(f"   找到 {len(tasks)} 件符合條件的維護案")
    send_line_message(tasks)
