import requests
import time

def get_chat_id(token):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    print(f"Checking for updates at: {url}")
    print("Please send a message 'Hello' to your bot on Telegram now...")
    
    while True:
        try:
            response = requests.get(url)
            data = response.json()
            
            if "result" in data and len(data["result"]) > 0:
                # Get the latest message
                latest = data["result"][-1]
                chat_id = latest["message"]["chat"]["id"]
                user_name = latest["message"]["chat"]["first_name"]
                
                print(f"\n✅ Success! Found message from {user_name}")
                print(f"🆔 YOUR CHAT_ID is: {chat_id}")
                return chat_id
            
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(2)
        print("Waiting for message...", end="\r")

if __name__ == "__main__":
    print("--- Telegram Chat ID Finder ---")
    token = input("Enter your Bot Token from BotFather: ").strip()
    if token:
        get_chat_id(token)
    else:
        print("Token cannot be empty.")
