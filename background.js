const llmKeywords = ["chat", "conversation"];

// map to track url's flagged via keywords
let possibleLLMEndpoints = new Set();

// check url's for keywords
chrome.webRequest.onBeforeRequest.addListener(
	function (details) {
		const url = details.url.toLowerCase();
		if (llmKeywords.some(keyword => url.includes(keyword))) {
			
			// store url in map
			possibleLLMEndpoints.add(details.requestId);
			console.log("Keyword match (possible LLM):", url);
		}
	},
	
	{ urls: ["<all_urls>"] },
	[]
);

// check flagged domains with header content-type
chrome.webRequest.onHeadersReceived.addListener(
	function (details) {
		if(!possibleLLMEndpoints.has(details.requestId)) return;
		
		const contentType = details.responseHeaders.find(
			(header) => header.name.toLowerCase() === "content-type"
		);
		
		if(contentType && (contentType.value.startsWith("text/event-stream")) || contentType.value.startsWith("application/json")) {
			console.log("LLM traffic confirmed:", details.url);
		}
		
		possibleLLMEndpoints.delete(details.requestId);
	},
	{ urls: ["<all_urls>"] },
	["responseHeaders"]
);