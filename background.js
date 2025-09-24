const llmKeywords = ["chat", "conversation"];

chrome.webRequest.onBeforeRequest.addListener(
	function(details) {
		const url = details.url.toLowerCase();
		
		//check for llm keywords
		if(llmKeywords.some(keyword => url.includes(keyword))){
			console.log("Possible LLM use detected:", url);
		}
	},
	{ urls: ["<all_urls>"] },
	[]
);