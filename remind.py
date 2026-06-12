import os
import requests

# ── 設定區 ──────────────────────────────────────────────
NOTION_TOKEN      = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

LINE_TOKEN        = os.environ["LINE_TOKEN"]
LINE_GROUP_ID     = os.environ["LINE_GROUP_ID"]
LINE_USER_ID      = os.environ["LINE_USER_ID"]   # 被標記的人的 userId

# Notion Database 中代表「未完成」的欄位設定
# 若你用 checkbox 欄位，把下面設為 checkbox 模式
# 若你用 Status 欄位（例如 "Status": "Not started"），改用 status 模式
FILTER_MODE       = "Status"   # "checkbox" 或 "status"
CHECKBOX_FIELD    = "Done"       # checkbox 欄位名稱（打勾=完成）
STATUS_FIELD      = "Status"     # status 欄位名稱
STATUS_INCOMPLETE = ["Not started", "In progress"]  # 視為未完成的值
TITLE_FIELD       = "Name"       # 任務標題的欄位名稱
# ────────────────────────────────────────────────────────


def fetch_incomplete_tasks():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    if FILTER_MODE == "checkbox":
        payload = {
            "filter": {
                "property": CHECKBOX_FIELD,
                "checkbox": {"equals": False},
            }
        }
    else:
        payload = {
            "filter": {
                "or": [
                    {"property": STATUS_FIELD, "status": {"equals": s}}
                    for s in STATUS_INCOMPLETE
                ]
            }
        }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    tasks = []
    for page in results:
        props = page.get("properties", {})
        title_prop = props.get(TITLE_FIELD, {})
        title_list = title_prop.get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_list).strip()
        if title:
            tasks.append(title)
    return tasks


def send_line_message(tasks):
    if not tasks:
        print("沒有未完成事項，略過傳送。")
        return

    task_lines = "\n".join(f"  • {t}" for t in tasks)
    message = (
        f"📋 每日待辦提醒\n"
        f"\u200b\n"               # zero-width space 讓 mention 之後換行更好看
        f"嗨 ${{mention}}，你還有 {len(tasks)} 件事項未完成：\n\n"
        f"{task_lines}\n\n"
        f"加油！💪"
    )

    # LINE Mention 格式：需要把 mention 嵌入 altText + contents
    payload = {
        "to": LINE_GROUP_ID,
        "messages": [
            {
                "type": "textV2",
                "text": f"📋 每日待辦提醒\n\n嗨 {{mention}}，你還有 {len(tasks)} 件事項未完成：\n\n{task_lines}\n\n加油！💪",
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
    print(f"✅ 已傳送提醒，共 {len(tasks)} 件待辦事項。")


if __name__ == "__main__":
    print("🔍 讀取 Notion 待辦事項...")
    tasks = fetch_incomplete_tasks()
    print(f"   找到 {len(tasks)} 件未完成事項")
    send_line_message(tasks)
