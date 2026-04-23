# 🎙️ ChatbotMP: Team Integration Guide

This guide contains everything the frontend team needs to integrate the AI RAG Chatbot into our website.

## 📍 API Endpoint
- **Base URL**: `https://braincache-bot.onrender.com`
- **Chat Endpoint**: `POST /chat`
- **Health Check**: `GET /health`

## 🔑 Authentication
All requests must include the following header for security:
`X-API-Key: dinesh-chatbot-key`

---

## 💻 Integration Example (Frontend)

```javascript
/* Standard Fetch Request */
async function getChatbotAnswer(userMessage) {
    const API_URL = "https://braincache-bot.onrender.com/chat";
    const API_KEY = "dinesh-chatbot-key";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            body: JSON.stringify({
                query: userMessage,
                userId: null, // Optional: pass a specific userId to filter content
                spaceId: null // Optional: pass a specific spaceId to filter content
            })
        });

        const result = await response.json();
        return result.answer;

    } catch (error) {
        console.error("Chatbot Error:", error);
        return "Sorry, I'm having trouble connecting to the brain right now.";
    }
}
```

---

## ⚡ Key System Features
- **Automatic Knowledge Sync**: The bot automatically synchronizes with our MongoDB every 10 minutes.
- **Context-Aware**: The bot knows which "Space" a piece of content belongs to and who the "Author" is.
- **Rate Limited**: The API is limited to 20 requests per minute per IP to prevent abuse.

---

## ✅ API Testing (cURL)
```bash
curl -X POST https://braincache-bot.onrender.com/chat \
     -H "X-API-Key: dinesh-chatbot-key" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is Machine Learning?"}'
```
