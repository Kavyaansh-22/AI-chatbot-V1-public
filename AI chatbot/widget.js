(function() {
    // Configuration
    // Ensure this URL is correct for local testing or deployment
    const API_URL = "http://127.0.0.1:8000/chat"; 
    
    // Inject CSS - Dark Theme, Sleek, Gemini-Inspired
    const style = document.createElement('style');
    style.innerHTML = `
        /* General Widget Container */
        #roadies-chat-widget { 
            position: fixed; 
            bottom: 20px; 
            right: 20px; 
            z-index: 9999; 
            font-family: 'Inter', sans-serif; /* Modern Font */
        }
        
        /* Chat Button (Floating Bubble) */
        #roadies-chat-btn { 
            width: 55px; 
            height: 55px; 
            background: #13f7cf; /* Bright Gemini Accent */
            border-radius: 50%; 
            box-shadow: 0 4px 15px rgba(19, 247, 207, 0.4); /* Glowing effect */
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #0d0d0d; 
            font-size: 24px; 
            transition: transform 0.3s ease-in-out; 
            font-weight: bold;
        }
        #roadies-chat-btn:hover { 
            transform: scale(1.05); 
            box-shadow: 0 4px 20px rgba(19, 247, 207, 0.7);
        }
        
        /* Chat Window */
        #roadies-chat-window { 
            width: 360px; 
            height: 550px; 
            background: #1e1e1e; /* Dark background */
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
            display: none; 
            flex-direction: column; 
            overflow: hidden; 
            position: absolute; 
            bottom: 75px; 
            right: 0; 
            border: 1px solid #282828;
        }
        
        /* Chat Header */
        .chat-header { 
            background: #0d0d0d; 
            color: #ffffff; 
            padding: 15px 20px; 
            font-weight: 600; 
            font-size: 16px;
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 1px solid #282828;
        }
        .chat-header span { font-size: 18px; }
        .chat-close { cursor: pointer; opacity: 0.7; transition: opacity 0.2s; }
        .chat-close:hover { opacity: 1; }
        
        /* Messages Area */
        .chat-messages { 
            flex: 1; 
            padding: 15px; 
            overflow-y: auto; 
            background: #1e1e1e; 
        }
        /* Scrollbar styling for dark theme (Webkit) */
        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 3px; }
        .chat-messages::-webkit-scrollbar-thumb:hover { background: #555; }

        .message { margin-bottom: 15px; display: flex; flex-direction: column; }
        .msg-bubble { 
            padding: 12px 18px; 
            border-radius: 18px; 
            max-width: 80%; 
            font-size: 14px; 
            line-height: 1.5; 
        }
        .user-msg { 
            align-self: flex-end; 
            background: #333333; 
            color: white; 
            border-bottom-right-radius: 4px; /* Sleek corner break */
        }
        .bot-msg { 
            align-self: flex-start; 
            background: #13f7cf; /* Accent color for bot */
            color: #0d0d0d; 
            font-weight: 500;
            border-bottom-left-radius: 4px; /* Sleek corner break */
        }
        
        /* Product Cards */
        .product-card { 
            background: #2a2a2a; /* Card background */
            border-radius: 8px; 
            padding: 10px; 
            margin-top: 10px; 
            display: flex; 
            gap: 12px; 
            align-items: center; 
            border: 1px solid #3a3a3a;
            color: #ffffff;
            transition: background 0.2s;
        }
        .product-card:hover {
            background: #333333;
        }
        .product-card img { 
            width: 60px; 
            height: 60px; 
            object-fit: cover; 
            border-radius: 6px; 
            border: 1px solid #13f7cf; /* Accent frame */
        }
        .product-info { display: flex; flex-direction: column; flex-grow: 1; }
        .product-name { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
        .product-price { color: #13f7cf; font-weight: bold; font-size: 13px; margin: 2px 0; }
        .product-link { 
            font-size: 12px; 
            color: #13f7cf; 
            text-decoration: none;
            transition: color 0.2s;
        }
        .product-link:hover { color: #ffffff; }

        /* Input Area */
        .chat-input-area { 
            padding: 12px; 
            border-top: 1px solid #282828; 
            display: flex; 
            background: #0d0d0d; 
        }
        #chat-input { 
            flex: 1; 
            border: none; 
            padding: 12px; 
            border-radius: 25px; 
            outline: none; 
            background: #333333; /* Input background */
            color: white;
            font-size: 14px;
            transition: box-shadow 0.2s;
        }
        #chat-input::placeholder {
            color: #888;
        }
        #chat-input:focus {
            box-shadow: 0 0 0 2px #13f7cf; /* Accent focus ring */
        }
        #chat-send { 
            background: #13f7cf; 
            color: #0d0d0d; 
            border: none; 
            padding: 8px 18px; 
            margin-left: 10px; 
            border-radius: 25px; 
            cursor: pointer; 
            font-weight: bold;
            transition: opacity 0.2s;
        }
        #chat-send:hover {
            opacity: 0.85;
        }
        
        /* Loading dots */
        .typing { 
            font-style: italic; 
            color: #13f7cf; 
            font-size: 12px; 
            margin-left: 15px; 
            margin-top: 5px;
            display:none;
        }
    `;
    document.head.appendChild(style);

    // Create Widget DOM (No changes here, remains the same structure)
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
                    <div class="msg-bubble bot-msg">Hi! I'm your Roadies expert. Looking for a high-safety helmet, jacket, or gloves today?</div>
                </div>
            </div>
            <div class="typing" id="typing-indicator">Roadies is typing...</div>
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Ask me about gear, price, or policy..." />
                <button id="chat-send">Send</button>
            </div>
        </div>
        <div id="roadies-chat-btn">🤖</div>
    `;
    document.body.appendChild(widgetContainer);

    // Event Listeners (Logic remains the same)
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
