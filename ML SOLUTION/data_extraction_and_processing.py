import json
import os
import pandas as pd

NON_LLM_DIR = 'har_data/non_llm_hars_sanitised'
NON_LLM_OUTPUT_CSV = "non_llm_har_parameters_dataset.csv"

LLM_DIR = "har_data/llm_hars"
LLM_OUTPUT_CSV = "llm_har_parameters_dataset.csv"


def extract_file_parameters(har_path):
	rows = []
	# try to load HAR file, return exception if fails
	try:
		with open(har_path, "r", encoding="utf-8") as file:
			har = json.load(file)
	except Exception as e:
		print(f"Error reading {har_path}:", {e})
		return rows
		
	# create list of entries in HAR file
	entries = har.get("log", {}).get("entries", [])
	if not isinstance(entries, list):
		return rows
	
	#loop through each entry in list, retrieve req and res
	for entry in entries:
		request = entry.get("request", {})
		response = entry.get("response", {})
		
		# flatten headers to dictionary, set all name's to lowercase
		req_header_dict = {h.get("name").lower(): h.get("value") for h in request.get("headers", []) if isinstance(h, dict)}
		res_header_dict = {h.get("name").lower(): h.get("value") for h in response.get("headers", []) if isinstance(h, dict)}
		
		url = request.get("url", "")
		authority = req_header_dict.get(":authority")
		path = req_header_dict.get(":path")
		
		if authority and path:
			website = authority
			filename = path
		elif authority:
			website = authority
			filename = "N/A"
		else:
			website = url
			filename = "N/A"
		
		method = request.get("method", "")
		req_length_str = req_header_dict.get("content-length", "")
		res_length_str = res_header_dict.get("content-length", "")
		res_size = response.get("content", {}).get("size", "")
		mime_type = response.get("content", {}).get("mimeType", "")
		
		# try to convert res/req length to int, else set to None
		try:
		    res_length = int(res_length_str)
		except (TypeError, ValueError):
		    res_length = None
		
		try:
		    req_length = int(req_length_str)
		except (TypeError, ValueError):
		    req_length = None
		
		has_content_length = res_length is not None
		
		rows.append({
			"file": os.path.basename(har_path),
			"website": website,
			"filename": filename,
			"method": method,
			"request_content_length": req_length,
			"response_content_length": res_length,
			"response_content_size": res_size,
			"mime_type": mime_type,
			"has_content_length": has_content_length
		})
	return rows

def process_files(dir):
	all_rows = []
	har_files = [f for f in os.listdir(dir) if f.endswith(".har")]
	print(f"Found {len(har_files)} HAR files in {dir}\n")
	
	for i, file in enumerate(har_files, start=1):
		har_path = os.path.join(dir, file)
		print(f"[{i:02d}/{len(har_files)}] Processing {file}...")
		rows = extract_file_parameters(har_path)
		all_rows.extend(rows)
		
	print(f"\n Extracted {len(all_rows)} entries from {len(har_files)} files")
	return all_rows
		
def main():
	non_llm_data = process_files(NON_LLM_DIR)
	non_llm_df = pd.DataFrame(non_llm_data)
	
	non_llm_df["is_post"] = non_llm_df["method"].eq("POST")
	non_llm_df["is_llm"] = "FALSE"
	
	print(f"💾 Saving non-llm dataset with {len(non_llm_df)} rows to {NON_LLM_OUTPUT_CSV}")
	non_llm_df.to_csv(NON_LLM_OUTPUT_CSV, index=False, encoding="utf-8")
	print("Done!")
	
	llm_data = process_files(LLM_DIR)
	llm_df = pd.DataFrame(llm_data)
	
	llm_df["is_post"] = llm_df["method"].eq("POST")
	llm_df["is_llm"] = "TRUE"
	
	print(f"💾 Saving llm dataset with {len(llm_df)} rows to {LLM_OUTPUT_CSV}")
	llm_df.to_csv(LLM_OUTPUT_CSV, index=False, encoding="utf-8")
	print("Done!")
	
if __name__ == "__main__":
    main()