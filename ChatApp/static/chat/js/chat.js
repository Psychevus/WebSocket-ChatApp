// Function to handle WebSocket connection setup
function setupWebSocket(conversationId, currentUser, emailUser) {
    const chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${conversationId}/`);

    chatSocket.addEventListener('error', (e) => {
        console.error('WebSocket error:', e);
    });

    chatSocket.addEventListener('message', (e) => {
        const message = JSON.parse(e.data);
        renderMessage(message, currentUser);
    });

    // Handle sending messages on form submission
    const chatForm = document.querySelector('#chat-form');
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const messageInputDom = document.querySelector('#message-input');
        const message = messageInputDom.value;

        chatSocket.send(JSON.stringify({
            message,
            sender_id: currentUser,
            sender_email: emailUser,
        }));

        messageInputDom.value = '';
    });

    // Scroll to the bottom when the page is loaded
    const chatMessages = document.querySelector('#chat-messages');
    window.addEventListener('load', () => {
        chatMessages.scrollIntoView({behavior: 'smooth', block: 'end'});
    });
}

// Function to render a message in the chat
function renderMessage(message, currentUser) {
    const chatMessages = document.querySelector('#chat-messages');
    const messageElement = document.createElement('li');
    messageElement.classList.add('flex', 'flex-row', message.sender_id === currentUser ? 'justify-end' : 'justify-start');

    const messageContainer = document.createElement('div');
    const containerClass = message.sender_id === currentUser ? 'right' : 'left';
    messageContainer.classList.add(`message-container-${containerClass}`);

    const messageBubble = document.createElement('div');
    messageBubble.classList.add('message-bubble');
    messageBubble.classList.add('shadow-xl');
    messageBubble.innerHTML = message.message;

    const timestamp = document.createElement('div');
    timestamp.classList.add('timestamp');
    timestamp.innerHTML = formatTimestamp(message.timestamp);

    messageBubble.appendChild(timestamp);
    messageContainer.appendChild(messageBubble);
    messageElement.appendChild(messageContainer);
    chatMessages.appendChild(messageElement);
    chatMessages.scrollIntoView({behavior: 'smooth', block: 'end'});
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
