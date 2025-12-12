(function() {
    // Configuration
    const API_URL = "http://127.0.0.1:8000/chat"; // Change to your Render URL later
    
    // Inject CSS
    const style = document.createElement('style');
    style.innerHTML = `
        #roadies-chat-widget { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Segoe UI', sans-serif; }
        #roadies-chat-btn { width: 60px; height: 60px; background: #e74c3c; border-radius: 50%; box-shadow: 0 4px 10px rgba(0,0,0,0.2); cursor: pointer; display: flex; align-items: center; justify-content: center; color: white; font-size: 30px; transition: transform 0.2s; }
        #roadies-chat-btn:hover { transform: scale(1.1); }
        
        #roadies-chat-window { width: 350px; height: 500px; background: white; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.15); display: none; flex-direction: column; overflow: hidden; position: absolute; bottom: 80px; right: 0; }
        .chat-header { background: #333; color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
        .chat-header span { font-size: 18px; }
        .chat-close { cursor: pointer; font-size: 20px; }
        
        .chat-messages { flex: 1; padding: 15px; overflow-y: auto; background: #f9f9f9; }
        .message { margin-bottom: 15px; display: flex; flex-direction: column; }
        .msg-bubble { padding: 10px 15px; border-radius: 15px; max-width: 85%; font-size: 14px; line-height: 1.4; }
        .user-msg { align-self: flex-end; background: #e74c3c; color: white; border-bottom-right-radius: 2px; }
        .bot-msg { align-self: flex-start; background: #e0e0e0; color: #333; border-bottom-left-radius: 2px; }
        
        .product-card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-top: 10px; display: flex; gap: 10px; align-items: center; }
        .product-card img { width: 50px; height: 50px; object-fit: cover; border-radius: 4px; }
        .product-info { display: flex; flex-direction: column; }
        .product-name { font-weight: bold; font-size: 13px; color: #333; }
        .product-price { color: #e74c3c; font-weight: bold; font-size: 12px; margin: 2px 0; }
        .product-link { font-size: 11px; color: #007bff; text-decoration: none; }
        
        .chat-input-area { padding: 10px; border-top: 1px solid #ddd; display: flex; background: white; }
        #chat-input { flex: 1; border: 1px solid #ddd; padding: 10px; border-radius: 20px; outline: none; }
        #chat-send { background: #333; color: white; border: none; padding: 8px 15px; margin-left: 10px; border-radius: 20px; cursor: pointer; }
        
        /* Loading dots */
        .typing { font-style: italic; color: #888; font-size: 12px; margin-left: 5px; display:none;}
    `;
    document.head.appendChild(style);

    // Create Widget DOM
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'roadies-chat-widget';
    widgetContainer.innerHTML = `
        <div id="roadies-chat-window">
            <div class="chat-header">
                <span>Roadies Gear Expert</span>
                <span class="chat-close">&times;</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="message">
                    <div class="msg-bubble bot-msg">Hi! I'm your Roadies expert. Looking for a helmet, jacket, or gloves today?</div>
                </div>
            </div>
            <div class="typing" id="typing-indicator">Roadies is typing...</div>
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Type a message..." />
                <button id="chat-send">Send</button>
            </div>
        </div>
        <div id="roadies-chat-btn">💬</div>
    `;
    document.body.appendChild(widgetContainer);

    // Event Listeners
    const chatBtn = document.getElementById('roadies-chat-btn');
    const chatWindow = document.getElementById('roadies-chat-window');
    const closeBtn = document.querySelector('.chat-close');
    const sendBtn = document.getElementById('chat-send');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');

    chatBtn.addEventListener('click', () => chatWindow.style.display = 'flex');
    closeBtn.addEventListener('click', () => chatWindow.style.display = 'none');

    // Send Message Logic
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Add User Message
        addMessage(text, 'user-msg');
        input.value = '';
        typingIndicator.style.display = 'block';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            
            typingIndicator.style.display = 'none';
            addMessage(data.reply, 'bot-msg');

            // Render Products if any
            if (data.products && data.products.length > 0) {
                const productContainer = document.createElement('div');
                productContainer.className = 'message';
                data.products.forEach(prod => {
                    const card = document.createElement('div');
                    card.className = 'product-card';
                    card.innerHTML = `
                        <img src="${prod.image}" alt="${prod.name}">
                        <div class="product-info">
                            <span class="product-name">${prod.name}</span>
                            <span class="product-price">₹${prod.price}</span>
                            <a href="${prod.link}" target="_blank" class="product-link">View Details &rarr;</a>
                        </div>
                    `;
                    productContainer.appendChild(card);
                });
                messagesContainer.appendChild(productContainer);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            addMessage("Sorry, I'm having trouble connecting to the garage. Please try again.", 'bot-msg');
        }
    }

    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';
        msgDiv.innerHTML = `<div class="msg-bubble ${className}">${text}</div>`;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

})();