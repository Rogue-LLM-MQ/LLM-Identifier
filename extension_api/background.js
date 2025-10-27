// set the api server url
const API_URL = "http://localhost:8000/predict"

// when request is completed, fire listener
chrome.webRequest.onCompleted.addListener(
	async (details) => {
		try {
			
			// pull headers and content length from details object
			const headers = details.responseHeaders || [];
			const contentLengthHeader = headers.find(h => h.name.toLowerCase() === 'content-length');
			
			// build json payload to send to prediction model
			const data = {
				method: details.method,
				request_content_length: details.requestBody ? details.requestBody.length : 0,
				response_content_length: contentLengthHeader ? parseInt(contentLengthHeader.value) : 0,
				response_content_size: details.responseSize || 0,
				has_content_length: !!contentLengthHeader,
				url_text: new URL(details.url).pathname
			};
			
			// send parameters to backend for prediction
			const res = await fetch(API_URL, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(data)
			});
			
			// if llm is detected, send notification
			if(result.is_llm){
				console.log("LLM TRAFFIC DETECTED:", details.url, "Confidence:", result.confidence);

		        chrome.notifications.create({
					type: "basic",
					iconUrl: "icon.png",
					title: "Possible LLM Traffic",
					message: `${details.url}\nConfidence: ${(result.confidence * 100).toFixed(1)}%`
				});
			}
		} catch (err) {
			console.error("Prediction error:", err);
		}
	},
	{ urls: ["<all_urls>"] },
	["responseHeaders"]
);
