import os
import json
import re

INPUT_DIR = "har_data/non_llm_hars"
OUTPUT_DIR = "har_data/non_llm_hars_sanitised"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_har_entry(entry):
    # remove IP addresses
    entry.pop("serverIPAddress", None)

    # remove cookies and other sensitive data from request
    if "request" in entry:
        req = entry["request"]

        req.pop("cookies", None)

        req["headers"] = [
            h for h in req.get("headers", [])
            if h["name"].lower() not in ("cookie", "authorization", "referer")
        ]

        if "postData" in req:
            if "text" in req["postData"]:
                req["postData"]["text"] = "[REDACTED]"

        req["queryString"] = [
            {"name": q["name"], "value": "[REDACTED]"} 
            for q in req.get("queryString", [])
        ]

    # remove cookies and other sensitive data from request
    if "response" in entry:
        res = entry["response"]

        res.pop("cookies", None)

        res["headers"] = [
            h for h in res.get("headers", [])
            if h["name"].lower() not in ("set-cookie", "location")
        ]

    return entry

# remove all instances of cookies (eg. nested and not previously removed)
def deep_remove_cookies(obj):
    if isinstance(obj, dict):
        obj.pop("cookies", None)
        for k, v in obj.items():
            deep_remove_cookies(v)
    elif isinstance(obj, list):
        for i in obj:
            deep_remove_cookies(i)

# save sanitised data in new file
for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".har"):
        continue

    in_path = os.path.join(INPUT_DIR, filename)
    out_path = os.path.join(OUTPUT_DIR, filename)

    with open(in_path, "r", encoding="utf-8") as f:
        try:
            har = json.load(f)
        except Exception as e:
            print(f"⚠️ Skipping {filename}: invalid JSON ({e})")
            continue

    try:
        entries = har.get("log", {}).get("entries", [])
        har["log"]["entries"] = [sanitize_har_entry(e) for e in entries]
        deep_remove_cookies(har)
    except Exception as e:
        print(f"⚠️ Error processing {filename}: {e}")
        continue

    # redact any IP-strings
    har_str = json.dumps(har)
    har_str = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', "[REDACTED_IP]", har_str)
    har = json.loads(har_str)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(har, f, ensure_ascii=False, indent=2)

    print(f"Sanitised: {filename}")

print("\nAll sanitised HARs saved to:", OUTPUT_DIR)