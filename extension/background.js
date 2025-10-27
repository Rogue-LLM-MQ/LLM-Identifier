const API_URL = "http://localhost:8000/predict";

// store recent URLS to track duplicates
const sentUrls = new Set();
const THROTTLE_MS = 500; // minimum time between sending the same URL

// clear recent URLs every minute
setInterval(() => {
  sentUrls.clear();
}, 60 * 1000);

// fire listener when new request is complete
chrome.webRequest.onCompleted.addListener(async (details) => {
  try {
	
    // filter sent requests to POST only
    if (details.method !== "POST") return;
    const url = new URL(details.url);

    // throttle duplicates
    const key = `${details.method}|${url.href}`;
    if (sentUrls.has(key)) return;
    sentUrls.add(key);

    // build payload to send to prediction model
    const headers = details.responseHeaders || [];
    const contentLengthHeader = headers.find(h => h.name.toLowerCase() === "content-length");

    const payload = {
	  is_post: details.method === "POST",
      request_content_length: 0, // PLACEHOLDER
      response_content_length: contentLengthHeader ? parseInt(contentLengthHeader.value) : 0,
      response_content_size: details.responseSize || 0,
      has_content_length: !!contentLengthHeader,
      url_text: url.pathname
    };

    // send to backend server
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

	// if LLM is detected, send to log with confidence
    if (result.is_llm) {
      console.log("LLM traffic detected:", details.url, "Confidence:", result.confidence);
    }

  } catch (err) {
    console.error("Error sending request to model:", err);
  }
}, { urls: ["<all_urls>"] }, ["responseHeaders"]);
