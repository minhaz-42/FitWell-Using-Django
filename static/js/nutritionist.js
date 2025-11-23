// NutriAI Assistant Chat functionality with BMI calculation support
class NutriAIChatAssistant {
    constructor() {
        this.chatForm = document.getElementById('chatForm');
        this.messageInput = document.getElementById('messageInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.bmiForm = document.getElementById('bmiForm');
        this.bmiResults = document.getElementById('bmiResults');
        this.conversationList = document.getElementById('conversationList');
        
        this.init();
    }

    init() {
        if (this.chatForm) {
            this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        }
        
        if (this.bmiForm) {
            this.bmiForm.addEventListener('submit', (e) => this.handleBMISubmit(e));
        }
        
        // Optional: Load conversation history if available
        this.loadConversationHistory();
    }

    async handleChatSubmit(e) {
        e.preventDefault();
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Show user message
        this.appendMessage('user', message);
        this.messageInput.value = '';

        try {
            const response = await this.sendChatMessage(message);
            if (response.success) {
                // Check if response includes BMI info
                if (response.bmi_data) {
                    this.displayBMIResults(response.bmi_data);
                }
                this.appendMessage('assistant', response.response);
            } else {
                throw new Error(response.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.appendMessage('error', 'Sorry, I encountered an error. Please try again.');
        }
    }

    async handleBMISubmit(e) {
        e.preventDefault();
        const formData = new FormData(this.bmiForm);
        const bmiData = {
            weight: parseFloat(formData.get('weight')),
            height: parseFloat(formData.get('height'))
        };

        try {
            const response = await this.calculateBMI(bmiData);
            if (response.success) {
                this.displayBMIResults(response.bmi_data);
            } else {
                throw new Error(response.error || 'Failed to calculate BMI');
            }
        } catch (error) {
            console.error('BMI calculation error:', error);
            this.showError('Failed to calculate BMI. Please try again.');
        }
    }

    async sendChatMessage(message) {
        const response = await fetch('/api/nutritionist/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                message: message,
                model: 'nutrition',
                language: 'en'
            })
        });

        return await response.json();
    }

    async calculateBMI(data) {
        const response = await fetch('/api/nutritionist/calculate-bmi', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        });

        return await response.json();
    }

    appendMessage(type, content) {
        if (!this.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(content)}
            </div>
            <div class="message-timestamp">
                ${new Date().toLocaleTimeString()}
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    displayBMIResults(bmiData) {
        if (!this.bmiResults) return;

        this.bmiResults.innerHTML = `
            <div class="bmi-result">
                <h3>BMI Results</h3>
                <div class="result-value">BMI: ${bmiData.bmi}</div>
                <div class="result-category">Category: ${bmiData.category}</div>
                <p class="result-message">${bmiData.message}</p>
                <div class="recommendations">
                    <h4>Recommendations:</h4>
                    <ul>
                        ${bmiData.recommendations.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    async loadConversationHistory() {
        if (!this.conversationList) return;

        try {
            const response = await fetch('/api/nutritionist/conversations');
            const conversations = await response.json();
            
            if (conversations.length) {
                this.conversationList.innerHTML = conversations.map(conv => `
                    <div class="conversation-item" data-id="${conv.id}">
                        <div class="conversation-title">${conv.title}</div>
                        <div class="conversation-preview">${conv.last_message}</div>
                        <div class="conversation-time">${conv.timestamp}</div>
                    </div>
                `).join('');
            } else {
                this.conversationList.innerHTML = '<p class="no-conversations">No conversation history yet.</p>';
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }

    formatMessage(content) {
        // Convert URLs to links
        content = content.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Handle line breaks
        return content.replace(/\n/g, '<br>');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        if (this.chatMessages) {
            this.chatMessages.appendChild(errorDiv);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    new NutriAIChatAssistant();
});
class AINutritionist {
    constructor() {
        this.chatForm = document.getElementById('chatForm');
        this.messageInput = document.getElementById('messageInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.conversationList = document.getElementById('conversationList');
        
        this.init();
    }

    init() {
        // Initialize chat functionality
        if (this.chatForm) {
            this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Load existing conversations if available
        this.loadConversations();
    }

    async handleSubmit(e) {
        e.preventDefault();
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Show user message immediately
        this.appendMessage(message, 'user');
        this.messageInput.value = '';

        try {
            const response = await fetch('/api/nutritionist/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    model: 'nutrition',
                    language: 'en'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.appendMessage(data.response, 'assistant');
                // Update conversation list
                this.loadConversations();
            } else {
                throw new Error(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.appendMessage('Sorry, I encountered an error. Please try again.', 'error');
        }
    }

    appendMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async loadConversations() {
        if (!this.conversationList) return;

        try {
            const response = await fetch('/api/nutritionist/conversations');
            const conversations = await response.json();
            
            this.conversationList.innerHTML = conversations.map(conv => `
                <div class="conversation-item" data-id="${conv.id}">
                    <h4>${conv.title}</h4>
                    <p>${conv.last_message}</p>
                    <span class="time">${conv.timestamp}</span>
                </div>
            `).join('');

            // Add click handlers
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.addEventListener('click', () => this.loadConversation(item.dataset.id));
            });
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }

    async loadConversation(conversationId) {
        try {
            const response = await fetch(`/api/nutritionist/conversations/${conversationId}`);
            const data = await response.json();
            
            this.chatMessages.innerHTML = '';
            data.messages.forEach(msg => {
                this.appendMessage(msg.message, msg.type);
            });
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    new AINutritionist();
});