import time
import json
import os
import requests
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# ---------------- CONFIG ----------------
KEYWORDS = [
    "gen ai",
    "generative ai",
    "artificial intelligence",
    "machine learning",
    "data scientist",
    "ai engineer",
    "ml engineer",
]

SENT_FILE = "sent_jobs.json"

SEARCH_URL = (
    "https://www.naukri.com/"
    "gen-ai-artificial-intelligence-machine-learning-data-scientist-jobs"
    "?experience=0&experience=2"
)

# TELEGRAM - Use environment variables for security in GitHub Actions
# You can set these in your local environment or in GitHub Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ---------------- TELEGRAM ----------------
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10,
        )
    except Exception as e:
        print(f"Error sending telegram message: {e}")


# ---------------- HELPERS ----------------
def load_sent_jobs():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_sent_jobs(jobs):
    with open(SENT_FILE, "w") as f:
        json.dump(list(jobs), f)


def keyword_match(title):
    t = title.lower()
    return any(k in t for k in KEYWORDS)


def random_sleep(min_sec=3, max_sec=7):
    time.sleep(random.uniform(min_sec, max_sec))


# ---------------- SELENIUM SETUP ----------------
options = Options()

# Automation-friendly flags
options.add_argument("--headless")  # Required for GitHub Actions
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")

# Random User Agent to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]
options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# Apply Stealth
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

wait = WebDriverWait(driver, 30)

# ---------------- MAIN ----------------
try:
    print("🚀 Naukri Job Alert Bot Started")
    # send("🚀 Naukri Job Alert Bot Started") # Optional: Disabled to reduce noise

    driver.get(SEARCH_URL)
    random_sleep(5, 10)

    # -------- Accept Cookies (CRITICAL) --------
    try:
        cookie_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_btn.click()
        random_sleep(2, 4)
    except:
        pass  # cookie may not appear every time

    # -------- Scroll to trigger loading --------
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    random_sleep(3, 6)

    # -------- Find job cards (MULTI-SELECTOR SAFE) --------
    jobs = []
    selectors = ["article.jobTuple", "div.jobTuple", "div.cust-job-tuple"]

    for sel in selectors:
        found = driver.find_elements(By.CSS_SELECTOR, sel)
        if found:
            jobs = found
            break

    if not jobs:
        print("⚠️ No jobs loaded. Naukri may have blocked or layout changed.")
        send("⚠️ No jobs loaded. Naukri may have blocked or layout changed.")
        driver.quit()
        exit()

    print(f"🔍 Found {len(jobs)} jobs on page")

    sent_jobs = load_sent_jobs()
    new_jobs_count = 0

    for job in jobs:
        try:
            title_el = job.find_element(By.CSS_SELECTOR, "a.title")
            title = title_el.text.strip()
            link = title_el.get_attribute("href")

            if link in sent_jobs:
                continue

            if not keyword_match(title):
                continue

            msg = f"🔔 New Job Alert\n\nTitle: {title}\n\nApply:\n{link}"
            send(msg)
            sent_jobs.add(link)
            new_jobs_count += 1
            print(f"✅ Sent: {title}")
            random_sleep(1, 3) # Delay between messages

        except Exception as e:
            continue

    save_sent_jobs(sent_jobs)
    print(f"✅ Job check completed. New jobs sent: {new_jobs_count}")
    # send(f"✅ Job check completed. New jobs sent: {new_jobs_count}") # Optional

finally:
    driver.quit()