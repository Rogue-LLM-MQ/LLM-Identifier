import json
import os
import pandas as pd

HAR_DIR = 'har_data/non_llm_hars_sanitised'

def get_post_ratio(har_path):
	get_count = 0
	post_count = 0
	other_count = 0
	total_count = 0
	
	with open(har_path, "r", encoding="utf-8") as file:
		har=json.load(file)
		
	entries = har.get("log", {}).get("entries", [])
	
	for entry in entries:
		total_count += 1
		
		method = entry.get("request", {}).get("method", "")
		
		if method == 'GET':
			get_count += 1
		
		if method == 'POST':
			post_count += 1
			
		if method != 'GET' and method != 'POST':
			print(method)
			
	get_percentage = (get_count/total_count)*100
	post_percentage = (post_count/total_count)*100
	
	print("GET: ", round(get_percentage, 2), " | POST: ", round(post_percentage, 2))

# helper function to set website and path seperately
def extract_site_and_path(req):
    headers = req.get("headers", [])
    url = req.get("url", "")

    req_header_dict = {h.get("name", "").lower(): h.get("value", "") for h in headers if isinstance(h, dict)}

    authority = req_header_dict.get(":authority")
    path = req_header_dict.get(":path")

	# if authority/path do not exist in headers, set website to complete url found under request
    if authority and path:
        website = authority
        filename = path
    elif authority:
        website = authority
        filename = "N/A"
    else:
        website = url
        filename = "N/A"

    return website, filename
	
def extract_parameters(har_path):
	# try to load HAR file, return exception if fails
	try:
		with open(har_path, "r", encoding="utf-8") as file:
			har = json.load(file)
	except Exception as e:
		print(f"Error reading {har_path}:", {e})
		return []
		
	# create list of entries in HAR file
	entries = har.get("log", {}).get("entries", [])
	
	#loop through each entry in list, retrieve req and res
	for entry in entries:
		request = entry.get("request", {})
		response = entry.get("response", {})
		
		req_headers = request.get("headers", [])
		res_headers = response.get("headers", [])
		
		# flatten headers to dictionary, set all name's to lowercase
		req_header_dict = {h.get("name").lower(): h.get("value") for h in req_headers if isinstance(h, dict)}
		res_header_dict = {h.get("name").lower(): h.get("value") for h in res_headers if isinstance(h, dict)}
		
		website, filename = extract_site_and_path(request)
		method = request.get("method", "")
		request_content_length = req_header_dict.get("content-length")
		response_content_length = res_header_dict.get("content-length")
		response_content_type = res_header_dict.get("content-type")
		
		print(website)
		print(filename)
		print(method)
		print(request_content_length)
		print(response_content_length)
		print(response_content_type)
		print("\n")
		
def main():
	extract_parameters(HAR_DIR + '/www.abc.net.au.har')
	
if __name__ == "__main__":
    main()