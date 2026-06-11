# 📋 LINE × Notion 每日待辦提醒機器人

每天自動讀取 Notion Database 的未完成事項，傳送到 LINE 群組並 @mention 指定成員。

---

## 🗂 專案結構

```
.
├── remind.py                        # 主程式
└── .github/workflows/daily-remind.yml  # GitHub Actions 排程
```

---

## ⚙️ 設定步驟

### Step 1 — 申請 LINE Messaging API

1. 前往 [LINE Developers Console](https://developers.line.biz/)，登入你的 LINE 帳號
2. 點 **Create a new provider**，隨便取個名字
3. 點 **Create a new channel** → 選 **Messaging API**
4. 填寫基本資料後建立
5. 進入 channel 後，前往 **Messaging API** 分頁：
   - 找到 **Channel access token**，點 **Issue** 產生 → 這是 `LINE_TOKEN`
   - 把機器人加入你的 LINE 群組（掃描 QR Code 加好友後，拉進群組）
6. 在 **Basic settings** 分頁關閉 **Auto-reply messages**（避免干擾）

### Step 2 — 取得 LINE Group ID 與 User ID

把機器人加入群組後，讓群組裡任何人傳一則訊息，  
然後用以下指令查詢 webhook 事件（需先在 LINE Developers 設定 Webhook URL，  
可以用 [webhook.site](https://webhook.site) 暫時接收）：

```json
{
  "events": [{
    "source": {
      "type": "group",
      "groupId": "Cxxxx...",   ← 這是 LINE_GROUP_ID
      "userId": "Uxxxx..."     ← 這是傳訊息那個人的 userId
    }
  }]
}
```

> 💡 要取得**被標記人的 userId**，請讓那個人在群組傳一則訊息，從 webhook 事件中讀取他的 `userId`。

### Step 3 — 設定 Notion Integration

1. 前往 [Notion Integrations](https://www.notion.so/my-integrations)
2. 點 **New integration**，取名並建立 → 複製 **Internal Integration Token**（`NOTION_TOKEN`）
3. 回到你的 Notion Database 頁面：
   - 點右上角 **⋯** → **Connections** → 加入剛才建立的 Integration
4. 從 Database 的 URL 複製 ID：  
   `https://notion.so/your-workspace/`**`這一段32字元就是DATABASE_ID`**`?v=...`

### Step 4 — 設定 GitHub Secrets

在你的 GitHub repo 前往 **Settings → Secrets and variables → Actions → New repository secret**，  
依序新增以下 5 個 Secret：

| Secret 名稱 | 說明 |
|---|---|
| `NOTION_TOKEN` | Notion Integration Token（`secret_...`）|
| `NOTION_DATABASE_ID` | Notion Database 的 32 字元 ID |
| `LINE_TOKEN` | LINE Channel Access Token |
| `LINE_GROUP_ID` | 群組 ID（`C` 開頭）|
| `LINE_USER_ID` | 被標記成員的 userId（`U` 開頭）|

### Step 5 — 調整設定（remind.py）

打開 `remind.py`，確認以下設定符合你的 Notion Database：

```python
FILTER_MODE    = "checkbox"  # 若用 Status 欄位改成 "status"
CHECKBOX_FIELD = "Done"      # 你的 checkbox 欄位名稱
TITLE_FIELD    = "Name"      # 你的標題欄位名稱
```

### Step 6 — 調整傳送時間

打開 `.github/workflows/daily-remind.yml`，修改 cron 時間：

```yaml
- cron: "0 1 * * *"   # UTC 時間，台灣早上 9:00 = UTC 01:00
```

常用時間對照（台灣時間 UTC+8）：

| 台灣時間 | cron (UTC) |
|---|---|
| 早上 8:00 | `0 0 * * *` |
| 早上 9:00 | `0 1 * * *` |
| 中午 12:00 | `0 4 * * *` |
| 下午 6:00 | `0 10 * * *` |

---

## 🧪 測試

設定完 Secrets 後，前往 GitHub Actions 頁面，  
找到 **Daily LINE Reminder**，點 **Run workflow** 手動觸發測試。

---

## 📝 注意事項

- LINE Messaging API 免費方案每月有 **200 則**免費訊息（對大多數提醒場景已足夠）
- 若 Notion Database 沒有未完成事項，程式會跳過傳送
- `textV2` 訊息類型支援 @mention，需要機器人在群組中有足夠權限
