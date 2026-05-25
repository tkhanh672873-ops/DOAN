/* ═══════════════════════════════════
   LOCAL CHATBOT LOGIC
═══════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

    const chatWidget = document.getElementById('chat-widget');
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const chatMessages = document.getElementById('chat-messages');
    const textarea = document.getElementById('chat-textarea');
    const sendBtn = document.getElementById('chat-send-btn');

    // Toggle chat
    toggleBtn.addEventListener('click', () => {
        chatWidget.classList.toggle('is-open');

        if (chatWidget.classList.contains('is-open')) {
            textarea.focus();
        }
    });

    // Auto resize
    textarea.addEventListener('input', function () {
        this.style.height = '44px';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';

        sendBtn.disabled = !this.value.trim();
    });

    // Enter gửi
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMessage(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    async function sendMessage() {

        const text = textarea.value.trim();

        if (!text) return;

        // reset input
        textarea.value = '';
        textarea.style.height = '44px';
        sendBtn.disabled = true;

        // user message
        const userHtml = `
            <div class="chat-msg user-msg">
                ${formatMessage(text)}
            </div>
        `;

        chatMessages.insertAdjacentHTML('beforeend', userHtml);

        scrollToBottom();

        // typing
        const typingId = 'typing-' + Date.now();

        chatMessages.insertAdjacentHTML('beforeend', `
            <div id="${typingId}" class="chat-typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `);

        scrollToBottom();

        try {

            // LOCAL API
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text
                })
            });

            const data = await res.json();

            // remove typing
            const typingEl = document.getElementById(typingId);

            if (typingEl) {
                typingEl.remove();
            }

            const botReply = data.reply || "Tôi chưa hiểu yêu cầu.";

            const botHtml = `
                <div class="chat-msg bot-msg">
                    ${formatMessage(botReply)}
                </div>
            `;

            chatMessages.insertAdjacentHTML('beforeend', botHtml);

        } catch (err) {

            const typingEl = document.getElementById(typingId);

            if (typingEl) {
                typingEl.remove();
            }

            chatMessages.insertAdjacentHTML('beforeend', `
                <div class="chat-msg bot-msg"
                     style="border:1px solid var(--danger-border);
                            background:var(--danger-bg);">
                    ⚠️ Không thể kết nối chatbot local.
                </div>
            `);
        }

        scrollToBottom();
    }

});