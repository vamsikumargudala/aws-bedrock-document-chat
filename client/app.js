// Configuration
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : '/api';

// State
let sessionId = null;
let messages = [];
let isStreaming = true;

// DOM Elements
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const charCount = document.getElementById('char-count');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');
const statusDetails = document.getElementById('status-details');
const sourcesList = document.getElementById('sources-list');
const sourcesSection = document.getElementById('sources-section');
const darkModeToggle = document.getElementById('dark-mode-toggle');
const streamModeToggle = document.getElementById('stream-mode');
const newChatBtn = document.getElementById('new-chat');
const clearChatBtn = document.getElementById('clear-chat');
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.querySelector('.sidebar');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing app...');
    initializeApp();
});

function initializeApp() {
    // Check if elements exist
    if (!messageInput || !sendBtn) {
        console.error('Required DOM elements not found');
        return;
    }

    // Generate session ID first
    sessionId = generateSessionId();
    console.log('Session ID:', sessionId);

    // Load preferences
    loadPreferences();

    // Check connection
    checkConnection();
    setInterval(checkConnection, 30000);

    // Setup event listeners
    setupEventListeners();

    // Auto-resize textarea
    autoResizeTextarea();

    // Enable send button if there's text
    sendBtn.disabled = true;
}

function loadPreferences() {
    // Dark mode
    const darkMode = localStorage.getItem('darkMode') === 'true';
    darkModeToggle.checked = darkMode;
    updateTheme(darkMode);

    // Stream mode
    const streamMode = localStorage.getItem('streamMode') !== 'false';
    streamModeToggle.checked = streamMode;
    isStreaming = streamMode;
}

function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Input changes
    messageInput.addEventListener('input', () => {
        charCount.textContent = messageInput.value.length;
        sendBtn.disabled = messageInput.value.trim().length === 0;
        autoResizeTextarea();
    });

    // Dark mode toggle
    darkModeToggle.addEventListener('change', (e) => {
        updateTheme(e.target.checked);
        localStorage.setItem('darkMode', e.target.checked);
    });

    // Stream mode toggle
    streamModeToggle.addEventListener('change', (e) => {
        isStreaming = e.target.checked;
        localStorage.setItem('streamMode', e.target.checked);
    });

    // New chat
    newChatBtn.addEventListener('click', startNewChat);

    // Clear chat
    clearChatBtn.addEventListener('click', clearChat);

    // Mobile menu toggle
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Suggested prompts
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('prompt-chip')) {
            messageInput.value = e.target.dataset.prompt;
            messageInput.focus();
            sendBtn.disabled = false;
            autoResizeTextarea();
        }
    });
}

function updateTheme(isDark) {
    if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.setAttribute('data-theme', 'light');
    }
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

function generateSessionId() {
    return 'session-' + Math.random().toString(36).substring(2, 11);
}

async function checkConnection() {
    try {
        console.log('Checking connection to:', `${API_BASE_URL}/health`);
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            mode: 'cors'
        });

        const data = await response.json();
        console.log('Connection response:', data);

        if (response.ok) {
            if (connectionStatus) {
                connectionStatus.classList.add('connected');
                connectionStatus.classList.remove('error');
            }
            if (statusText) {
                statusText.textContent = 'Connected';
            }
            if (statusDetails && data.client_type) {
                statusDetails.textContent = `Using ${data.client_type === 'agent' ? 'Bedrock Agent' : 'Knowledge Base'}`;
            }
        }
    } catch (error) {
        console.error('Connection error:', error);
        if (connectionStatus) {
            connectionStatus.classList.add('error');
            connectionStatus.classList.remove('connected');
        }
        if (statusText) {
            statusText.textContent = 'Connection failed';
        }
        if (statusDetails) {
            statusDetails.textContent = error.message;
        }
    }
}

function startNewChat() {
    sessionId = generateSessionId();
    messages = [];
    messagesContainer.innerHTML = createWelcomeMessage();
    sourcesList.innerHTML = '';
    sourcesSection.style.display = 'none';
}

function clearChat() {
    messagesContainer.innerHTML = createWelcomeMessage();
    messages = [];
}

function createWelcomeMessage() {
    return `
        <div class="welcome-message">
            <h2>Welcome to RAG Assistant</h2>
            <p>Ask questions about your documents and get intelligent answers powered by AWS Bedrock.</p>
            <div class="suggested-prompts">
                <button class="prompt-chip" data-prompt="What documents do you have access to?">
                    What documents are available?
                </button>
                <button class="prompt-chip" data-prompt="Give me a summary of the main topics">
                    Summarize main topics
                </button>
                <button class="prompt-chip" data-prompt="Help me understand the key concepts">
                    Explain key concepts
                </button>
            </div>
        </div>
    `;
}

function addMessage(content, type = 'assistant', isHTML = false) {
    // Remove welcome message if present
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (isHTML) {
        contentDiv.innerHTML = content;
    } else {
        contentDiv.textContent = content;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return contentDiv;
}

function createLoadingMessage() {
    const loadingHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    return addMessage(loadingHTML, 'assistant', true);
}

function displaySources(sources) {
    displaySourcesWithReferences(sources);
}

function addInlineCitations(content, sources) {
    if (!sources || sources.length === 0) {
        return content;
    }

    // Add inline citations at the end of paragraphs or sentences
    let modifiedContent = content;

    // Add citations as superscript numbers with links
    const citationsHtml = sources.map((source, index) => {
        const citationNumber = index + 1;
        if (source.url || (source.source && source.source.startsWith('http'))) {
            const url = source.url || source.source;
            const title = source.title || source.source?.split('/').pop() || 'Source';
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="citation-link" title="${title}">[${citationNumber}]</a>`;
        }
        return `<span class="citation-number">[${citationNumber}]</span>`;
    }).join(' ');

    // Add citations at the end of the content
    if (citationsHtml) {
        modifiedContent += ` ${citationsHtml}`;
    }

    return modifiedContent;
}

function displaySourcesWithReferences(sources) {
    if (!sourcesSection || !sourcesList) {
        console.warn('Sources section elements not found');
        return;
    }

    if (!sources || sources.length === 0) {
        sourcesSection.style.display = 'none';
        return;
    }

    sourcesSection.style.display = 'block';
    sourcesList.innerHTML = '';

    sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-item';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'source-header';

        const nameDiv = document.createElement('div');
        nameDiv.className = 'source-name';

        // Extract filename from S3 URI or use full path
        let displayName = 'Unknown source';
        if (source.source || source.url) {
            const uri = source.source || source.url;
            displayName = uri.split('/').pop() || uri;
        } else if (source.title) {
            displayName = source.title;
        }

        nameDiv.textContent = `${index + 1}. ${displayName}`;
        headerDiv.appendChild(nameDiv);

        // Add reference link if available
        if (source.url || (source.source && source.source.startsWith('http'))) {
            const linkDiv = document.createElement('div');
            linkDiv.className = 'source-link';

            const link = document.createElement('a');
            link.href = source.url || source.source;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = '🔗 View Source';
            link.className = 'reference-link';

            linkDiv.appendChild(link);
            headerDiv.appendChild(linkDiv);
        }

        sourceDiv.appendChild(headerDiv);

        // Remove content preview/snippet display

        // Add author if available
        if (source.author) {
            const authorDiv = document.createElement('div');
            authorDiv.className = 'source-author';
            authorDiv.textContent = `Author: ${source.author}`;
            sourceDiv.appendChild(authorDiv);
        }

        // Remove relevance score display

        sourcesList.appendChild(sourceDiv);
    });
}

let isProcessing = false;

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;

    // Add user message
    addMessage(message, 'user');
    messages.push({ role: 'user', content: message });

    // Clear input
    messageInput.value = '';
    charCount.textContent = '0';
    sendBtn.disabled = true;
    autoResizeTextarea();

    try {
        // Send to API
        if (isStreaming) {
            await sendStreamingMessage(message);
        } else {
            await sendRegularMessage(message);
        }
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

async function sendRegularMessage(message) {
    const loadingMessage = createLoadingMessage();

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                max_results: 5,
                stream: false,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get response');
        }

        const data = await response.json();

        // Remove loading message
        loadingMessage.parentElement.remove();

        // Add response with markdown and inline citations
        const formattedContent = marked.parse(data.answer);
        const contentWithCitations = addInlineCitations(formattedContent, data.sources);
        const responseDiv = addMessage(contentWithCitations, 'assistant', true);

        // Apply syntax highlighting
        responseDiv.querySelectorAll('pre code').forEach((block) => {
            Prism.highlightElement(block);
        });

        // Display sources
        displaySources(data.sources);

        // Save to messages
        messages.push({ role: 'assistant', content: data.answer });

    } catch (error) {
        loadingMessage.parentElement.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    }
}

async function sendStreamingMessage(message) {
    // Start with loading dots
    const loadingDiv = createLoadingMessage();
    let fullResponse = '';
    let sources = [];
    let responseDiv = null;
    let hasCreatedResponseDiv = false;

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                max_results: 5,
                stream: true,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'metadata') {
                            sources = data.sources || [];
                            // Create response div only once when we get first data
                            if (!hasCreatedResponseDiv && loadingDiv && loadingDiv.parentElement) {
                                loadingDiv.parentElement.remove();
                                responseDiv = addMessage('', 'assistant');
                                hasCreatedResponseDiv = true;
                            }
                        } else if (data.type === 'content') {
                            // Create response div only once if not already created
                            if (!hasCreatedResponseDiv) {
                                if (loadingDiv && loadingDiv.parentElement) {
                                    loadingDiv.parentElement.remove();
                                }
                                responseDiv = addMessage('', 'assistant');
                                hasCreatedResponseDiv = true;
                            }

                            // Add the new text chunk to full response
                            fullResponse += data.text;

                            // Update content word by word - parse markdown and update immediately
                            if (responseDiv) {
                                const formattedContent = marked.parse(fullResponse);
                                // Add inline citations to the response
                                const contentWithCitations = addInlineCitations(formattedContent, sources);
                                responseDiv.innerHTML = contentWithCitations;

                                // Apply syntax highlighting to any new code blocks
                                responseDiv.querySelectorAll('pre code').forEach((block) => {
                                    if (!block.classList.contains('hljs')) {
                                        Prism.highlightElement(block);
                                    }
                                });

                                // Scroll to bottom smoothly
                                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                            }
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e);
                    }
                }
            }
        }

        // Display sources with reference links
        displaySourcesWithReferences(sources);

        // Save to messages
        messages.push({ role: 'assistant', content: fullResponse });

    } catch (error) {
        // Remove loading if still present
        if (loadingDiv && loadingDiv.parentElement) {
            loadingDiv.parentElement.remove();
        }
        addMessage(`Error: ${error.message}`, 'assistant');
    }
}

// This is handled in setupEventListeners, removing duplicate