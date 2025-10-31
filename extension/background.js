const API_ENDPOINT = "http://localhost:8000/predict";

// temporary cache of request metadata by requestId
const requestCache = new Map();

// capture request metadata before request is sent (using onBeforeReqiest instead of onCompleted)
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    // estimate request body size
    let reqSize = 0;
    if (details.requestBody) {
      if (details.requestBody.raw) {
        reqSize = details.requestBody.raw.reduce(
          (sum, part) => sum + (part.bytes ? part.bytes.byteLength : 0),
          0
        );
      }
    }

    requestCache.set(details.requestId, {
      method: details.method,
      request_content_length: reqSize,
    });
  },
  { urls: ["<all_urls>"] },
  ["requestBody"]
);

// capture remaining parameters after request is complete
chrome.webRequest.onCompleted.addListener(
  async (details) => {
    // ignore requests to localhost to prevent recursion
    if (details.url.startsWith(API_ENDPOINT) || details.url.includes("localhost:8000")) {
      return;
    }

    // lookup cached request metadata
    const reqData = requestCache.get(details.requestId) || {};
    requestCache.delete(details.requestId);

    // determine URL path only (remove domain)
    const urlObj = new URL(details.url);
    const urlText = urlObj.pathname || "/";

    // extract content-length
    let contentLengthHeader = details.responseHeaders?.find(
      (h) => h.name.toLowerCase() === "content-length"
    );
    const respLen = contentLengthHeader ? parseInt(contentLengthHeader.value) : 0;

    // construct payload for prediction model
    const payload = {
      is_post: details.method === "POST",
      request_content_length: reqData.request_content_length || 0,
      response_content_length: respLen,
      response_content_size: details.responseSize || 0,
      has_content_length: contentLengthHeader !== undefined,
      url_text: urlText,
    };

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (result.is_llm) {
        console.warn("LLM traffic detected:", details.url, "Confidence:", result.confidence);
      }
    } catch (err) {
      console.error("Prediction API error:", err);
    }
  },
  { urls: ["<all_urls>"] },
  ["responseHeaders"]
);