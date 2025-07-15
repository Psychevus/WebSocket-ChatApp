// Function to handle WebSocket connection setup
function setupWebSocket(conversationId, currentUser, emailUser) {
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/${conversationId}/`);
    let keyPair = null;
    let sharedSecret = null;

    chatSocket.addEventListener('error', (e) => {
        console.error('WebSocket error:', e);
    });

    chatSocket.addEventListener('open', () => {
        if (window.nacl) {
            keyPair = nacl.box.keyPair();
            chatSocket.send(JSON.stringify({type: 'public_key', key: nacl.util.encodeBase64(keyPair.publicKey)}));
        }
    });

    chatSocket.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'typing') {
            showTypingIndicator(data.sender_email);
            return;
        }

        if (data.type === 'public_key' && keyPair) {
            if (data.sender_id !== currentUser) {
                const otherKey = nacl.util.decodeBase64(data.key);
                sharedSecret = nacl.box.before(otherKey, keyPair.secretKey);
            }
            return;
        }

        if (data.nonce && data.message && sharedSecret) {
            const nonce = nacl.util.decodeBase64(data.nonce);
            const ciphertext = nacl.util.decodeBase64(data.message);
            const decrypted = nacl.box.open.after(ciphertext, nonce, sharedSecret);
            if (decrypted) {
                data.message = nacl.util.encodeUTF8(decrypted);
            } else {
                console.error('Failed to decrypt message');
                return;
            }
        }

        renderMessage(data, currentUser);
    });

    // Handle sending messages on form submission
    const chatForm = document.querySelector('#chat-form');
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const messageInputDom = document.querySelector('#message-input');
        const message = messageInputDom.value;

        if (sharedSecret) {
            const nonce = nacl.randomBytes(nacl.box.nonceLength);
            const ciphertext = nacl.box.after(nacl.util.decodeUTF8(message), nonce, sharedSecret);
            chatSocket.send(JSON.stringify({
                nonce: nacl.util.encodeBase64(nonce),
                message: nacl.util.encodeBase64(ciphertext),
                sender_id: currentUser,
                sender_email: emailUser,
            }));
        } else {
            chatSocket.send(JSON.stringify({
                message,
                sender_id: currentUser,
                sender_email: emailUser,
            }));
        }

        messageInputDom.value = '';
        messageInputDom.focus();
    });

    const messageInput = document.querySelector('#message-input');
    let typingTimeout;
    messageInput.addEventListener('input', () => {
        chatSocket.send(JSON.stringify({ type: 'typing' }));
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            chatSocket.send(JSON.stringify({ type: 'typing' }));
        }, 1000);
    });

    // Scroll to the bottom when the page is loaded
    const chatMessages = document.querySelector('#chat-messages');
    window.addEventListener('load', () => {
        chatMessages.scrollIntoView({behavior: 'smooth', block: 'end'});
        const messageInputDom = document.querySelector('#message-input');
        messageInputDom.focus();
    });
}

function setupRoomWebSocket(roomId, currentUser, emailUser) {
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/rooms/${roomId}/`);
    let keyPair = null;
    let sharedSecret = null;

    chatSocket.addEventListener('error', (e) => {
        console.error('WebSocket error:', e);
    });

    chatSocket.addEventListener('open', () => {
        if (window.nacl) {
            keyPair = nacl.box.keyPair();
            chatSocket.send(JSON.stringify({type: 'public_key', key: nacl.util.encodeBase64(keyPair.publicKey)}));
        }
    });

    chatSocket.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'typing') {
            showTypingIndicator(data.sender_email);
            return;
        }

        if (data.type === 'public_key' && keyPair) {
            if (data.sender_id !== currentUser) {
                const otherKey = nacl.util.decodeBase64(data.key);
                sharedSecret = nacl.box.before(otherKey, keyPair.secretKey);
            }
            return;
        }

        if (data.nonce && data.message && sharedSecret) {
            const nonce = nacl.util.decodeBase64(data.nonce);
            const ciphertext = nacl.util.decodeBase64(data.message);
            const decrypted = nacl.box.open.after(ciphertext, nonce, sharedSecret);
            if (decrypted) {
                data.message = nacl.util.encodeUTF8(decrypted);
            } else {
                console.error('Failed to decrypt message');
                return;
            }
        }

        renderMessage(data, currentUser);
    });

    const chatForm = document.querySelector('#chat-form');
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const messageInputDom = document.querySelector('#message-input');
        const message = messageInputDom.value;

        if (sharedSecret) {
            const nonce = nacl.randomBytes(nacl.box.nonceLength);
            const ciphertext = nacl.box.after(nacl.util.decodeUTF8(message), nonce, sharedSecret);
            chatSocket.send(JSON.stringify({
                nonce: nacl.util.encodeBase64(nonce),
                message: nacl.util.encodeBase64(ciphertext),
                sender_id: currentUser,
                sender_email: emailUser,
            }));
        } else {
            chatSocket.send(JSON.stringify({
                message,
                sender_id: currentUser,
                sender_email: emailUser,
            }));
        }

        messageInputDom.value = '';
        messageInputDom.focus();
    });

    const messageInput = document.querySelector('#message-input');
    let typingTimeout;
    messageInput.addEventListener('input', () => {
        chatSocket.send(JSON.stringify({ type: 'typing' }));
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            chatSocket.send(JSON.stringify({ type: 'typing' }));
        }, 1000);
    });

    const chatMessages = document.querySelector('#chat-messages');
    window.addEventListener('load', () => {
        chatMessages.scrollIntoView({behavior: 'smooth', block: 'end'});
        const messageInputDom = document.querySelector('#message-input');
        messageInputDom.focus();
    });
}

// Function to render a message in the chat
function renderMessage(message, currentUser, depth = 0, container) {
    const chatMessages = container || document.querySelector('#chat-messages');
    const messageElement = document.createElement('li');
    messageElement.classList.add('flex', 'flex-row', message.sender_id === currentUser ? 'justify-end' : 'justify-start');
    if (depth > 0) {
        messageElement.style.marginLeft = `${depth * 20}px`;
    }

    const messageContainer = document.createElement('div');
    const containerClass = message.sender_id === currentUser ? 'right' : 'left';
    messageContainer.classList.add(`message-container-${containerClass}`);

    const messageBubble = document.createElement('div');
    messageBubble.classList.add('message-bubble');
    messageBubble.classList.add('shadow-xl');
    messageBubble.textContent = message.message;

    const timestamp = document.createElement('div');
    timestamp.classList.add('timestamp');
    timestamp.innerHTML = formatTimestamp(message.timestamp);

    if (message.expires_at) {
        const chip = document.createElement('span');
        chip.classList.add('expiry-chip');
        messageBubble.appendChild(chip);
        const end = new Date(message.expires_at);
        const interval = setInterval(() => {
            const remaining = Math.floor((end - Date.now()) / 1000);
            if (remaining <= 0) {
                messageElement.remove();
                clearInterval(interval);
                return;
            }
            chip.textContent = `${remaining}s`;
        }, 1000);
    }

    messageBubble.appendChild(timestamp);

    if (message.reactions) {
        const reactions = document.createElement('div');
        Object.entries(message.reactions).forEach(([emoji, count]) => {
            const span = document.createElement('span');
            span.textContent = `${emoji} ${count}`;
            span.style.marginRight = '4px';
            reactions.appendChild(span);
        });
        if (reactions.childNodes.length) {
            messageBubble.appendChild(reactions);
        }
    }

    messageContainer.appendChild(messageBubble);
    messageElement.appendChild(messageContainer);
    chatMessages.appendChild(messageElement);
    chatMessages.scrollIntoView({behavior: 'smooth', block: 'end'});

    if (message.children) {
        message.children.forEach(child => renderMessage(child, currentUser, depth + 1, chatMessages));
    }
}

function showTypingIndicator(senderEmail) {
    const typingElement = document.getElementById('typing-indicator');
    if (!typingElement) return;
    typingElement.textContent = `${senderEmail} is typing...`;
    typingElement.style.display = 'block';
    clearTimeout(typingElement._timeout);
    typingElement._timeout = setTimeout(() => {
        typingElement.style.display = 'none';
    }, 1000);
}

// Function to format the timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${month}/${day}/${year} ${hours}:${minutes}`;
}


// Get conversation ID and current user data from the HTML attributes
const conversationElement = document.getElementById('conversation-data');
const currentUserElement = document.getElementById('currentuser-data');
const emailUserElement = document.getElementById('emailuser-data');

if (conversationElement && currentUserElement && emailUserElement) {
    const conversationId = parseInt(conversationElement.getAttribute('data-conversation-id'));
    const currentUser = parseInt(currentUserElement.getAttribute('data-currentuser-id'));
    const emailUser = emailUserElement.getAttribute('data-emailuser-id');

    // Initialize WebSocket connection
    setupWebSocket(conversationId, currentUser, emailUser);
}

const roomElement = document.getElementById('room-data');
if (roomElement && currentUserElement && emailUserElement) {
    const roomId = parseInt(roomElement.getAttribute('data-room-id'));
    const currentUser = parseInt(currentUserElement.getAttribute('data-currentuser-id'));
    const emailUser = emailUserElement.getAttribute('data-emailuser-id');
    setupRoomWebSocket(roomId, currentUser, emailUser);
}
