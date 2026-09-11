import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


# ========================================
# 設定
# ========================================

PRODUCT_URL = "https://www.sofmap.com/product_detail.aspx?sku=102321925"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

CHECK_INTERVAL = 300  # 5分


# ========================================
# 在庫状態を確認
# ========================================

def check_stock(page):

    print("商品ページを確認しています...")

    try:
        page.goto(
            PRODUCT_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(3000)

        text = page.locator("body").inner_text()

        # 予約終了
        if "限定数終了" in text:
            return "sold_out"

        # 予約受付中
        if "予約受付開始" in text:
            return "available"

        # 判断できない
        return "unknown"

    except Exception as e:

        print("ページ確認中にエラーが発生しました")
        print(e)

        return "unknown"


# ========================================
# 前回の状態を読み込む
# ========================================

def load_previous_state():

    try:
        with open("state.txt", "r", encoding="utf-8") as f:
            return f.read().strip()

    except FileNotFoundError:

        return None


# ========================================
# 現在の状態を保存
# ========================================

def save_state(state):

    with open("state.txt", "w", encoding="utf-8") as f:
        f.write(state)


# ========================================
# Discord通知
# ========================================

def send_discord():

    message = (
        "🚨 Nintendo Switch 2 ゼルダ40周年ケース\n"
        "予約可能になりました！\n\n"
        f"{PRODUCT_URL}"
    )

    data = {
        "content": message
    }

    response = requests.post(
        WEBHOOK_URL,
        json=data,
        timeout=30
    )

    if response.status_code == 204:

        print("Discord通知：成功")

    else:

        print("Discord通知：失敗")
        print(response.text)


# ========================================
# メイン処理
# ========================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    print("================================")
    print("ゼルダケース予約監視を開始します")
    print("監視間隔：5分")
    print("================================")

    while True:

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print()
        print("確認時刻:", now)

        # 現在の状態を確認
        current_state = check_stock(page)

        print("現在の状態:", current_state)

        # 前回の状態を取得
        previous_state = load_previous_state()

        print("前回の状態:", previous_state)

        # --------------------------------
        # 初回
        # --------------------------------

        if previous_state is None:

            print("初回確認です。状態を保存します。")

            save_state(current_state)

        # --------------------------------
        # 売り切れ → 予約可能
        # --------------------------------

        elif (
            previous_state == "sold_out"
            and current_state == "available"
        ):

            print()
            print("★★★★★★★★★★★★★★★★")
            print("予約可能になりました！！！")
            print("★★★★★★★★★★★★★★★★")

            send_discord()

            save_state(current_state)

        # --------------------------------
        # 通常
        # --------------------------------

        elif current_state != "unknown":

            save_state(current_state)

        else:

            print("状態を判定できなかったため、前回状態を維持します。")

        # --------------------------------
        # 5分待つ
        # --------------------------------

        print()
        print("次回確認まで5分待ちます...")

        time.sleep(CHECK_INTERVAL)
        
