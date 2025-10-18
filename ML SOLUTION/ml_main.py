import os
import json
import pandas as pd

HAR_DIR = "har_data/non_llm_hars_sanitised"
OUTPUT_CSV = "har_headers_dataset.csv"

def extract_request_headers(har_path):
    """Extract request header info from a HAR file."""
    try:
        with open(har_path, "r", encoding="utf-8") as f:
            har = json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading {har_path}: {e}")
        return []

    entries = har.get("log", {}).get("entries", [])
    data = []

    for entry in entries:
        req = entry.get("request", {})
        res = entry.get("response", {})

        url = req.get("url", "")
        method = req.get("method", "")
        status = res.get("status", None)
        mime = res.get("content", {}).get("mimeType", "")
        headers = req.get("headers", [])

        # Flatten headers into a single dictionary
        header_dict = {h.get("name"): h.get("value") for h in headers if isinstance(h, dict)}

        # Build row with some common metadata
        row = {
            "filename": os.path.basename(har_path),
            "method": method,
            "status": status,
            "mimeType": mime,
            "url": url,
            **header_dict  # expands into columns like "User-Agent", "Accept", etc.
        }

        data.append(row)

    return data


def main():
    all_rows = []
    har_files = [f for f in os.listdir(HAR_DIR) if f.endswith(".har")]

    print(f"📂 Found {len(har_files)} HAR files in {HAR_DIR}\n")

    for i, file in enumerate(har_files, start=1):
        har_path = os.path.join(HAR_DIR, file)
        print(f"[{i:02d}/{len(har_files)}] Processing {file} ...")
        rows = extract_request_headers(har_path)
        all_rows.extend(rows)

    # Create DataFrame
    df = pd.DataFrame(all_rows)

    print(f"\n✅ Extracted {len(df)} total requests across {len(har_files)} HAR files")

    # Optional: drop duplicates or NaNs
    df.dropna(axis=1, how="all", inplace=True)

    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"💾 Saved results to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()