const chatBtn = document.getElementById('chat-btn');
const chatContainer = document.getElementById('chat-container');

chatBtn.addEventListener('click', function() {
    chatContainer.style.display = (chatContainer.style.display === 'none' || chatContainer.style.display === '') ? 'block' : 'none';
});
