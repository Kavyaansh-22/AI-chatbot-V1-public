(function() {
    // Configuration
    const API_URL = "http://localhost:8000/chat"; 
    
    // --- BIKER THEME CSS VARIABLES (INJECTED) ---
    const style = document.createElement('style');
    style.innerHTML = `
        :root {
            /* General Theme: NEON CRIMSON / DARK GREY */
            --color-bg-primary: #1C1C1C; /* Dark Grey/Black */
            --color-bg-secondary: #2C2C2C; /* Chat Window BG base */
            --color-accent: #FF4D4D; /* NEON RED/CRIMSON - Primary Accent */
            --color-accent-light: #ff7f7f; /* Lighter shade of red */
            --color-text-primary: #F0F0F0;
            --color-text-secondary: #AAAAAA;
            --color-shadow: #000000;
            --font-family: 'Montserrat', 'Inter', sans-serif;
            --radius-sm: 8px;
            --radius-lg: 16px;

            /* Chat Bubbles */
            --color-bubble-bot: #3A3A3A; /* Dark bubble */
            --color-bubble-user: #0066CC; /* Deep Blue user bubble (For high contrast) */
            --color-card-bg: rgba(44, 44, 44, 0.6); /* Semi-transparent card */
        }

        /* --- Global Reset and Font --- */
        #roadies-chat-widget * {
            box-sizing: border-box;
            font-family: var(--font-family);
            color: var(--color-text-primary);
        }

        /* --- 1. Floating Widget Container --- */
        #roadies-chat-widget { 
            position: fixed; 
            bottom: 20px; 
            right: 20px; 
            z-index: 9999; 
            font-family: var(--font-family);
        }

        /* --- 2. Chat Button (Floating Bubble) --- */
        #roadies-chat-btn { 
            width: 60px; 
            height: 60px; 
            background: var(--color-accent);
            border-radius: 50%; 
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: var(--color-text-primary); 
            font-size: 28px; 
            transition: all 0.3s ease; 
            font-weight: bold;
            border: none;
        }
        #roadies-chat-btn:hover { 
            transform: scale(1.05); 
            background: var(--color-accent-light);
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 77, 77, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 77, 77, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 77, 77, 0); }
        }
        #roadies-chat-btn:not(.active):not(:hover) {
            animation: pulse 2s infinite;
        }

        /* --- 3. Chat Window (Glassmorphism Panel) --- */
        #roadies-chat-window { 
            width: 380px; 
            height: 500px; 
            max-width: 90vw;
            max-height: 80vh;
            background: rgba(44, 44, 44, 0.9);
            border-radius: var(--radius-lg); 
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex; 
            visibility: hidden; 
            flex-direction: column; 
            overflow: hidden; 
            position: absolute; 
            bottom: 80px; 
            right: 0; 
            border: 1px solid var(--color-bubble-bot);
            
            transform: scale(0.95) translateY(10px); 
            opacity: 0;
            transition: opacity 0.3s ease, transform 0.3s ease, visibility 0.3s;
        }
        #roadies-chat-window.open {
            visibility: visible;
            opacity: 1;
            transform: scale(1) translateY(0);
        }

        /* Full screen on mobile */
        @media (max-width: 600px) {
            #roadies-chat-window {
                width: 100vw;
                height: 100vh;
                max-width: 100vw;
                max-height: 100vh;
                bottom: 0;
                right: 0;
                border-radius: 0;
            }
        }
        
        /* --- 4. Chat Header and Messages --- */
        .chat-header { 
            background: rgba(35, 35, 35, 0.8); 
            color: var(--color-accent); 
            padding: 12px 18px; 
            font-weight: 800; 
            font-size: 1.1em;
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 1px solid var(--color-bubble-bot);
        }
        .chat-close { cursor: pointer; opacity: 0.8; transition: opacity 0.2s; font-size: 1.5em; font-weight: 300; }
        .chat-close:hover { opacity: 1; }

        .chat-messages { flex: 1; padding: 15px; overflow-y: auto; background: var(--color-bg-primary); scroll-behavior: smooth; }
        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
        .chat-messages::-webkit-scrollbar-thumb:hover { background: #777; }

        .message { margin-bottom: 12px; display: flex; flex-direction: column; }
        
        .msg-bubble { 
            padding: 12px 16px; 
            border-radius: var(--radius-sm); 
            max-width: 85%; 
            font-size: 14px; 
            line-height: 1.5; 
            opacity: 0;
            transform: translateY(10px);
            animation: slideIn 0.3s forwards;
        }
        @keyframes slideIn {
            to { opacity: 1; transform: translateY(0); }
        }

        .user-msg { align-self: flex-end; background: var(--color-bubble-user); color: var(--color-text-primary); border-bottom-right-radius: 4px; }
        .bot-msg { align-self: flex-start; background: var(--color-bubble-bot); color: var(--color-text-primary); font-weight: 400; border-bottom-left-radius: 4px; }
        
        /* Product Cards, Prompts, Input Area, Typing Indicator */
        .product-card-container { margin-bottom: 15px; }
        .product-card { background: var(--color-card-bg); border-radius: var(--radius-sm); padding: 12px; margin-top: 10px; display: flex; gap: 12px; align-items: center; border: 1px solid rgba(255, 77, 77, 0.2); box-shadow: 0 2px 5px rgba(0, 0, 0, 0.4); transition: all 0.2s ease; }
        .product-card:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(255, 77, 77, 0.2); background: rgba(58, 58, 58, 0.8); }
        .product-card img { width: 55px; height: 55px; object-fit: cover; border-radius: 4px; border: 1px solid var(--color-accent); }
        .product-info { display: flex; flex-direction: column; flex-grow: 1; }
        .product-name { font-weight: 600; font-size: 14px; color: var(--color-accent-light); }
        .product-price { color: var(--color-text-primary); font-weight: bold; font-size: 13px; margin: 2px 0; }
        /* Link color is the main accent red/crimson */
        .product-link { font-size: 12px; color: var(--color-accent); text-decoration: none; font-weight: 600; }
        .product-link:hover { color: var(--color-text-primary); }

        /* Suggested Prompts use red accent */
        .suggestions-container { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 15px 12px; background: var(--color-bg-primary); }
        .suggested-prompt-btn { background: rgba(255, 77, 77, 0.15); color: var(--color-accent-light); border: 1px solid var(--color-accent); padding: 8px 12px; border-radius: 20px; font-size: 0.8em; cursor: pointer; transition: background 0.2s, transform 0.1s; white-space: nowrap; font-weight: 600; }
        .suggested-prompt-btn:hover { background: rgba(255, 77, 77, 0.3); transform: translateY(-1px); }

        .chat-input-area { padding: 12px; border-top: 1px solid var(--color-bubble-bot); display: flex; background: rgba(35, 35, 35, 0.9); }
        #chat-input { flex: 1; border: none; padding: 10px 15px; border-radius: 20px; outline: none; background: var(--color-bubble-bot); color: var(--color-text-primary); font-size: 14px; transition: box-shadow 0.2s; }
        #chat-input:focus { box-shadow: 0 0 0 2px var(--color-accent); }
        
        /* Send button uses the main red accent */
        #chat-send { background: var(--color-accent); color: var(--color-bg-primary); border: none; padding: 10px 18px; margin-left: 10px; border-radius: 20px; cursor: pointer; font-weight: 800; transition: background 0.2s; }
        #chat-send:hover:not(:disabled) { background: var(--color-accent-light); }
        #chat-send:disabled { background: #5A5A5A; cursor: not-allowed; }
        
        .typing { font-style: italic; color: var(--color-accent); font-size: 12px; margin-left: 15px; margin-top: 5px; margin-bottom: 5px; display:none; }
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
                </div>
            <div class="typing" id="typing-indicator">Roadies is calculating the best route...</div>
            
            <div class="suggestions-container" id="suggestions-container"></div> 
            
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Ask about safety, touring, or budget..." />
                <button id="chat-send">Send</button>
            </div>
        </div>
        <button id="roadies-chat-btn">🏍️</button>
    `;
    document.body.appendChild(widgetContainer);

    // --- Core Logic & Event Listeners ---
    
    // Global State
    const chatBtn = document.getElementById('roadies-chat-btn');
    const chatWindow = document.getElementById('roadies-chat-window');
    const closeBtn = document.querySelector('.chat-close');
    const sendBtn = document.getElementById('chat-send');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const suggestionsContainer = document.getElementById('suggestions-container');
    
    const SESSION_ID = 'user-' + Math.random().toString(36).substring(2, 9); 
    
    // Flag to track if the greeting has been displayed in the current session
    let greetingDisplayed = false; 

    // Helper to inject message and handle animation delay
    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';
        const msgBubble = document.createElement('div');
        msgBubble.className = `msg-bubble ${className}`;
        msgBubble.textContent = text;
        msgBubble.style.animationDelay = '0.1s';
        
        msgDiv.appendChild(msgBubble);
        messagesContainer.appendChild(msgDiv);
    }
    
    // **GREETING FUNCTION**
    function displayInitialGreeting() {
        if (greetingDisplayed) return;

        addMessage("Welcome to Roadies, the gear shop for the open road! How may I assist you with finding your perfect helmet, jacket, or gloves today?", 'bot-msg');
        renderSuggestions(["Find helmets under ₹6 000", "Show jackets for touring", "Explain DOT vs ECE"]);
        
        greetingDisplayed = true;
    }


    // **TOGGLE FUNCTION (Opening/Closing)**
    chatBtn.addEventListener('click', () => {
        const isOpen = chatWindow.classList.toggle('open');
        chatBtn.classList.toggle('active', isOpen); 

        if (isOpen) {
            displayInitialGreeting();
            messagesContainer.scrollTop = messagesContainer.scrollHeight; 
        }
    });
    
    closeBtn.addEventListener('click', () => {
        chatWindow.classList.remove('open');
        chatBtn.classList.remove('active');
    });


    // Function to render suggested prompts
    function renderSuggestions(prompts) {
        suggestionsContainer.innerHTML = ''; 
        if (!prompts || prompts.length === 0) return;

        prompts.forEach(promptText => {
            const btn = document.createElement('button');
            btn.className = 'suggested-prompt-btn';
            btn.textContent = promptText;
            btn.addEventListener('click', () => {
                sendMessage(promptText);            
                suggestionsContainer.innerHTML = ''; 
            });
            suggestionsContainer.appendChild(btn);
        });
        messagesContainer.scrollTop = messagesContainer.scrollHeight; 
    }


    // **SEND MESSAGE LOGIC (Robust State Management)**
    async function sendMessage(textFromPrompt = null) {
        const text = textFromPrompt || input.value.trim();
        if (!text) return;

        suggestionsContainer.innerHTML = ''; 

        // State update: Add User Message and Show Loading
        addMessage(text, 'user-msg');
        input.value = '';
        
        // Disable input/button immediately
        input.disabled = true;
        sendBtn.disabled = true;
        typingIndicator.style.display = 'block';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: SESSION_ID })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // State update: Hide Loading
            typingIndicator.style.display = 'none';
            
            // 1. Add Bot Reply
            addMessage(data.reply, 'bot-msg');

            // 2. Render Products 
            if (data.products && data.products.length > 0) {
                const productContainer = document.createElement('div');
                productContainer.className = 'product-card-container';
                data.products.forEach((prod, index) => {
                    const card = document.createElement('div');
                    card.className = 'product-card';
                    card.style.animationDelay = `${0.3 + index * 0.1}s`;
                    card.innerHTML = `
                        <img src="${prod.image}" alt="${prod.name}">
                        <div class="product-info">
                            <span class="product-name">${prod.name}</span>
                            <span class="product-price">₹${prod.price.toLocaleString('en-IN')}</span>
                            <a href="${prod.link}" target="_blank" class="product-link">View Details &rarr;</a>
                        </div>
                    `;
                    productContainer.appendChild(card);
                });
                messagesContainer.appendChild(productContainer);
            }
            
            // 3. Render Suggested Prompts
            if (data.suggested_prompts && data.suggested_prompts.length > 0) {
                renderSuggestions(data.suggested_prompts);
            }

        } catch (error) {
            console.error('Roadies AI Error (Network/API failure):', error);
            typingIndicator.style.display = 'none';
            // Provide a detailed error message for better debugging
            addMessage(`Transmission failed! I cannot reach your backend server at ${API_URL}. Please ensure your 'main.py' script is running and accessible.`, 'bot-msg');
            renderSuggestions(["Try again", "What gear do you sell?"]);
        } finally {
            // CRITICAL: This block ensures the UI is always re-enabled, even if an error occurred.
            input.disabled = false;
            sendBtn.disabled = false;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Wiring up input/send button to the main logic
    sendBtn.addEventListener('click', () => sendMessage());
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

})();
