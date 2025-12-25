import requests
import json
import time

# You might need to install this: pip install apig-sdk
# Or use standard requests with headers if your endpoint allows it.

# --- 1. CONFIGURATION ---
# You get these from the Huawei Cloud Console -> ModelArts -> Service Deployment
REAL_MODE = True  # Set to False if you want to test offline
ENDPOINT_URL = "https://<your-modelarts-endpoint>/v1/infers/..."
APP_KEY = "YOUR_APP_KEY"
APP_SECRET = "YOUR_APP_SECRET"


def generate_answer_with_mindspore(context, question):
    """
    Sends the prompt to your deployed MindSpore model on ModelArts.
    """
    if not REAL_MODE:
        # Fallback for demo if internet is down
        return f"**[Simulated MindSpore]** Based on '{context[:20]}...', the answer is..."

    # 1. Prepare the Prompt
    prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"

    # 2. Prepare Payload (Matches what your MindSpore model expects)
    # Usually strictly JSON
    payload = {
        "input_text": prompt,
        "parameters": {
            "max_length": 100,
            "temperature": 0.7
        }
    }

    # 3. Create Headers (Huawei usually uses X-Auth-Token or AppKey/Secret)
    # For a competition demo, simple Token auth is often easiest if enabled.
    headers = {
        "Content-Type": "application/json",
        "X-Apig-AppCode": "YOUR_APP_CODE_IF_USING_APIG"
        # OR if using IAM Token: "X-Auth-Token": "YOUR_IAM_TOKEN"
    }

    try:
        # 4. SEND REQUEST TO CLOUD
        print("⚡ Connecting to Huawei Cloud ModelArts...")
        response = requests.post(ENDPOINT_URL, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            # Parse the result (depends on your model's output format)
            # Example: {"result": "The answer is X"}
            return result.get('result', result)
        else:
            print(f"Cloud Error: {response.status_code} - {response.text}")
            return "⚠️ ModelArts is currently unreachable. (Status: " + str(response.status_code) + ")"

    except Exception as e:
        print(f"Connection Failed: {e}")
        return "⚠️ Error connecting to Huawei Cloud. Please check internet connection."