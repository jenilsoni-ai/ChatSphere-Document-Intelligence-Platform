/**
 * ChatSphere Widget
 * This script creates and manages the chatbot widget on the client's website.
 */

(function() {
  // Debug mode
  const DEBUG = true;
  
  // Debug logging function
  function debugLog(message, type = 'log') {
    if (!DEBUG) return;
    
    const prefix = '[ChatSphere Widget]';
    
    switch (type) {
      case 'error':
        console.error(`${prefix} ${message}`);
        break;
      case 'warn':
        console.warn(`${prefix} ${message}`);
        break;
      case 'info':
        console.info(`${prefix} ${message}`);
        break;
      default:
        console.log(`${prefix} ${message}`);
    }
    
    // Check if we're on the debug page and update the log
    try {
      const debugEl = document.getElementById('debug-log');
      if (debugEl) {
        const entry = document.createElement('div');
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${prefix} ${message}`;
        if (type === 'error') entry.className = 'error';
        if (type === 'info') entry.className = 'success';
        debugEl.appendChild(entry);
        debugEl.scrollTop = debugEl.scrollHeight;
      }
    } catch (e) {
      // Ignore errors in debug logging
    }
  }

  // Initialization started
  debugLog('Widget script loaded', 'info');
  
  // Get the current script tag
  let scriptTag;
  try {
    scriptTag = document.currentScript;
    debugLog(`Script tag found: ${scriptTag ? 'yes' : 'no'}`);
  } catch (e) {
    debugLog(`Error getting currentScript: ${e.message}`, 'error');
    
    // Fallback: find the script tag with our data attribute
    const scripts = document.querySelectorAll('script[data-chatbot-id]');
    if (scripts.length > 0) {
      scriptTag = scripts[scripts.length - 1]; // Use the last one if multiple exist
      debugLog(`Fallback script tag found with data attribute`);
    } else {
      // Try to find by source containing "/widget/"
      const allScripts = document.querySelectorAll('script');
      for (let i = 0; i < allScripts.length; i++) {
        if (allScripts[i].src && allScripts[i].src.includes('/widget/')) {
          scriptTag = allScripts[i];
          debugLog(`Found script tag by URL pattern: ${scriptTag.src}`);
          break;
        }
      }
    }
  }
  
  if (!scriptTag) {
    debugLog('Unable to find script tag. Widget cannot initialize.', 'error');
    return;
  }
  
  // Extract chatbot ID and configuration from data attributes
  let chatbotId = scriptTag.getAttribute('data-chatbot-id');
  if (!chatbotId) {
    // Try to extract from URL if not provided as attribute
    try {
      const urlParts = scriptTag.src.split('/');
      chatbotId = urlParts[urlParts.length - 1].replace('.js', '');
      debugLog(`Extracted chatbot ID from URL: ${chatbotId}`);
    } catch (e) {
      debugLog(`Error extracting chatbot ID from URL: ${e.message}`, 'error');
    }
  }
  
  if (!chatbotId) {
    debugLog('No chatbot ID found. Widget cannot initialize.', 'error');
    return;
  }
  
  debugLog(`Chatbot ID: ${chatbotId}`);
  
  const defaultPosition = scriptTag.getAttribute('data-position') || 'bottom-right';
  const defaultPrimaryColor = '#' + (scriptTag.getAttribute('data-primary-color') || '6366f1');
  const defaultTitle = scriptTag.getAttribute('data-title') || 'Chat Assistant';
  const showBranding = scriptTag.getAttribute('data-show-branding') !== 'false';
  
  debugLog(`Initial configuration: position=${defaultPosition}, color=${defaultPrimaryColor}, title=${defaultTitle}, branding=${showBranding}`);
  
  // API Base URL - infer from script source
  const scriptSrc = scriptTag.src;
  debugLog(`Script source: ${scriptSrc}`);
  
  let apiBase;
  try {
    // Determine API base URL based on script source
    const scriptUrl = new URL(scriptSrc);
    const port = scriptUrl.port;
    
    if (port === '8000') {
        debugLog('Detected direct backend access on port 8000');
        apiBase = scriptUrl.origin;
    } else if (port === '3000') {
        debugLog('Detected frontend proxy on port 3000');
        apiBase = 'http://localhost:8000';
    } else {
        debugLog('Using default API base');
        apiBase = 'http://localhost:8000';
    }
  } catch (e) {
    debugLog(`Error determining API base URL: ${e.message}`, 'error');
    
    // Fallback to window location if script URL parsing failed
    try {
      apiBase = window.location.origin;
      debugLog(`Falling back to window location origin: ${apiBase}`);
    } catch (e2) {
      // Final fallback
      apiBase = 'http://localhost:8000';
      debugLog(`Falling back to default API Base URL: ${apiBase}`);
    }
  }
  
  // Widget state
  let widgetState = {
    open: false,
    messages: [],
    inputValue: '',
    loading: false,
    initialized: false,
    sessionId: null
  };
  
  // Create and append the widget styles
  function addStyles() {
    debugLog('Adding widget styles');
    const styleTag = document.createElement('style');
    styleTag.id = 'chatsphere-widget-styles';
    styleTag.innerHTML = `
      .chatsphere-widget-container {
        position: fixed;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        transition: all 0.3s ease;
        box-sizing: border-box;
      }
      .chatsphere-widget-container * {
        box-sizing: border-box;
      }
      .chatsphere-widget-container.bottom-right {
        bottom: 20px;
        right: 20px;
      }
      .chatsphere-widget-container.bottom-left {
        bottom: 20px;
        left: 20px;
      }
      .chatsphere-widget-container.top-right {
        top: 20px;
        right: 20px;
      }
      .chatsphere-widget-container.top-left {
        top: 20px;
        left: 20px;
      }
      .chatsphere-widget-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
      }
      .chatsphere-widget-button:hover {
        transform: scale(1.05);
      }
      .chatsphere-widget-button svg {
        width: 30px;
        height: 30px;
        fill: white;
      }
      .chatsphere-widget-card {
        position: absolute;
        bottom: 80px;
        width: 350px;
        height: 500px;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
        background-color: white;
        transition: all 0.3s ease;
        opacity: 0;
        transform: translateY(20px);
        pointer-events: none;
      }
      .chatsphere-widget-container.bottom-right .chatsphere-widget-card {
        right: 0;
      }
      .chatsphere-widget-container.bottom-left .chatsphere-widget-card {
        left: 0;
      }
      .chatsphere-widget-container.top-right .chatsphere-widget-card {
        right: 0;
        bottom: auto;
        top: 80px;
      }
      .chatsphere-widget-container.top-left .chatsphere-widget-card {
        left: 0;
        bottom: auto;
        top: 80px;
      }
      .chatsphere-widget-card.open {
        opacity: 1;
        transform: translateY(0);
        pointer-events: all;
      }
      .chatsphere-widget-header {
        padding: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
      }
      .chatsphere-widget-header-title {
        font-weight: 600;
        font-size: 16px;
      }
      .chatsphere-widget-header-close {
        cursor: pointer;
        opacity: 0.8;
        transition: opacity 0.2s ease;
      }
      .chatsphere-widget-header-close:hover {
        opacity: 1;
      }
      .chatsphere-widget-header-close svg {
        width: 16px;
        height: 16px;
        fill: white;
      }
      .chatsphere-widget-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        background-color: #f9fafb;
      }
      .chatsphere-widget-message {
        max-width: 80%;
        padding: 12px;
        border-radius: 12px;
        line-height: 1.5;
        font-size: 14px;
        animation: messageAppear 0.3s ease forwards;
      }
      @keyframes messageAppear {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .chatsphere-widget-message.user {
        align-self: flex-end;
        background-color: #6366f1;
        color: white;
        border-bottom-right-radius: 4px;
      }
      .chatsphere-widget-message.bot {
        align-self: flex-start;
        background-color: white;
        border: 1px solid #e5e7eb;
        color: #374151;
        border-bottom-left-radius: 4px;
      }
      .chatsphere-widget-message-sources {
        margin-top: 8px;
        font-size: 12px;
        color: #9ca3af;
      }
      .chatsphere-widget-message-source-link {
        color: #6366f1;
        text-decoration: underline;
        cursor: pointer;
      }
      .chatsphere-widget-input-container {
        padding: 12px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        gap: 8px;
      }
      .chatsphere-widget-input {
        flex: 1;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        outline: none;
        font-size: 14px;
      }
      .chatsphere-widget-input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 1px #6366f1;
      }
      .chatsphere-widget-send-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: background-color 0.2s ease;
        padding: 0;
        background-color: transparent;
      }
      .chatsphere-widget-send-button:hover {
        background-color: rgba(99, 102, 241, 0.1);
      }
      .chatsphere-widget-send-button svg {
        width: 20px;
        height: 20px;
      }
      .chatsphere-widget-loading {
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: center;
        padding: 12px;
      }
      .chatsphere-widget-loading-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #6366f1;
        animation: loadingPulse 1.5s infinite ease-in-out;
      }
      .chatsphere-widget-loading-dot:nth-child(2) {
        animation-delay: 0.2s;
      }
      .chatsphere-widget-loading-dot:nth-child(3) {
        animation-delay: 0.4s;
      }
      @keyframes loadingPulse {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1); }
      }
      .chatsphere-widget-branding {
        text-align: center;
        font-size: 12px;
        padding: 8px;
        color: #9ca3af;
      }
      .chatsphere-widget-branding a {
        color: #6366f1;
        text-decoration: none;
      }
    `;
    try {
      document.head.appendChild(styleTag);
      debugLog('Styles added successfully', 'info');
    } catch (e) {
      debugLog(`Error adding styles: ${e.message}`, 'error');
    }
  }
  
  // Create the widget elements
  function createWidget(config) {
    debugLog('Creating widget with config: ' + JSON.stringify(config));
    
    try {
      // Main container
      const container = document.createElement('div');
      container.className = `chatsphere-widget-container ${config.position}`;
      container.id = 'chatsphere-widget-container';
      
      // Chat toggle button
      const button = document.createElement('div');
      button.className = 'chatsphere-widget-button';
      button.id = 'chatsphere-widget-button';
      button.style.backgroundColor = config.primaryColor;
      button.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-message-circle"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
      `;
      
      // Chat card
      const card = document.createElement('div');
      card.className = 'chatsphere-widget-card';
      card.id = 'chatsphere-widget-card';
      
      // Card header
      const header = document.createElement('div');
      header.className = 'chatsphere-widget-header';
      header.style.backgroundColor = config.primaryColor;
      header.innerHTML = `
        <div class="chatsphere-widget-header-title">${config.title}</div>
        <div class="chatsphere-widget-header-close" id="chatsphere-widget-close">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </div>
      `;
      
      // Messages container
      const messages = document.createElement('div');
      messages.className = 'chatsphere-widget-messages';
      messages.id = 'chatsphere-widget-messages';
      
      // Input container
      const inputContainer = document.createElement('div');
      inputContainer.className = 'chatsphere-widget-input-container';
      
      const input = document.createElement('input');
      input.className = 'chatsphere-widget-input';
      input.id = 'chatsphere-widget-input';
      input.type = 'text';
      input.placeholder = 'Type your message...';
      
      const sendButton = document.createElement('button');
      sendButton.className = 'chatsphere-widget-send-button';
      sendButton.id = 'chatsphere-widget-send';
      sendButton.style.color = config.primaryColor;
      sendButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-send"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
      `;
      
      inputContainer.appendChild(input);
      inputContainer.appendChild(sendButton);
      
      // Add branding if enabled
      if (config.showBranding) {
        const branding = document.createElement('div');
        branding.className = 'chatsphere-widget-branding';
        branding.innerHTML = 'Powered by <a href="https://chatsphere.app" target="_blank">ChatSphere</a>';
        card.appendChild(branding);
      }
      
      // Assemble the card
      card.appendChild(header);
      card.appendChild(messages);
      card.appendChild(inputContainer);
      
      // Assemble the widget
      container.appendChild(button);
      container.appendChild(card);
      
      // Add to document
      document.body.appendChild(container);
      debugLog('Widget elements created and added to DOM', 'info');
      
      // Setup event listeners
      setupEventListeners();
  
      // Add initial message if available
      if (config.initialMessage) {
        addMessage('bot', config.initialMessage);
      }
  
      // Mark as initialized
      widgetState.initialized = true;
      debugLog('Widget initialization complete', 'info');
    } catch (e) {
      debugLog(`Error creating widget: ${e.message}`, 'error');
    }
  }
  
  // Add a message to the chat
  function addMessage(role, content, sources = []) {
    debugLog(`Adding message: role=${role}, content=${content.substring(0, 30)}...`);
    
    try {
      const messagesContainer = document.getElementById('chatsphere-widget-messages');
      if (!messagesContainer) {
        debugLog('Messages container not found', 'error');
        return;
      }
      
      const messageEl = document.createElement('div');
      messageEl.className = `chatsphere-widget-message ${role}`;
      messageEl.textContent = content;
      
      // Add sources if available
      if (sources && sources.length > 0) {
        debugLog(`Adding ${sources.length} sources to message`);
        
        const sourcesEl = document.createElement('div');
        sourcesEl.className = 'chatsphere-widget-message-sources';
        sourcesEl.innerHTML = 'Sources: ';
        
        sources.forEach((source, index) => {
          const sourceLink = document.createElement('a');
          sourceLink.className = 'chatsphere-widget-message-source-link';
          sourceLink.textContent = `[${index + 1}]`;
          sourceLink.title = source.title || source.url;
          sourceLink.href = source.url;
          sourceLink.target = '_blank';
          
          sourcesEl.appendChild(sourceLink);
          
          if (index < sources.length - 1) {
            sourcesEl.appendChild(document.createTextNode(', '));
          }
        });
        
        messageEl.appendChild(sourcesEl);
      }
      
      messagesContainer.appendChild(messageEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      
      // Store message in state
      widgetState.messages.push({ role, content, sources });
    } catch (e) {
      debugLog(`Error adding message: ${e.message}`, 'error');
    }
  }
  
  // Show loading indicator
  function showLoading() {
    debugLog('Showing loading indicator');
    widgetState.loading = true;
    
    try {
      const messagesContainer = document.getElementById('chatsphere-widget-messages');
      if (!messagesContainer) {
        debugLog('Messages container not found', 'error');
        return;
      }
      
      const loadingEl = document.createElement('div');
      loadingEl.className = 'chatsphere-widget-loading';
      loadingEl.id = 'chatsphere-widget-loading';
      
      for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'chatsphere-widget-loading-dot';
        loadingEl.appendChild(dot);
      }
      
      messagesContainer.appendChild(loadingEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (e) {
      debugLog(`Error showing loading indicator: ${e.message}`, 'error');
    }
  }
  
  // Hide loading indicator
  function hideLoading() {
    debugLog('Hiding loading indicator');
    widgetState.loading = false;
    
    try {
      const loadingEl = document.getElementById('chatsphere-widget-loading');
      if (loadingEl) {
        loadingEl.remove();
      }
    } catch (e) {
      debugLog(`Error hiding loading indicator: ${e.message}`, 'error');
    }
  }
  
  // Toggle widget open/closed
  function toggleWidget() {
    try {
      const card = document.getElementById('chatsphere-widget-card');
      if (!card) {
        debugLog('Chat card not found', 'error');
        return;
      }
      
      widgetState.open = !widgetState.open;
      debugLog(`Toggling widget: ${widgetState.open ? 'open' : 'closed'}`);
      
      if (widgetState.open) {
        card.classList.add('open');
        document.getElementById('chatsphere-widget-input').focus();
      } else {
        card.classList.remove('open');
      }
    } catch (e) {
      debugLog(`Error toggling widget: ${e.message}`, 'error');
    }
  }
  
  // Send a message to the chatbot API
  async function sendMessage(message) {
    if (!message.trim() || widgetState.loading) {
      debugLog('Empty message or widget is loading, ignoring send request');
      return;
    }
    
    debugLog(`Sending message: ${message.substring(0, 30)}...`);
    
    // Add user message to chat
    addMessage('user', message);
    
    try {
      // Clear input
      document.getElementById('chatsphere-widget-input').value = '';
      widgetState.inputValue = '';
      
      // Show loading
      showLoading();
      
      // Call the chat API
      const chatApiEndpoint = `/api/chat/widget/${chatbotId}`;
      const fullApiUrl = `${apiBase}${chatApiEndpoint}`;
      
      debugLog(`Calling API: ${fullApiUrl}`);
      
      const response = await fetch(fullApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          sessionId: widgetState.sessionId
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        debugLog(`API error (${response.status}): ${errorText}`, 'error');
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      debugLog(`Received response from API: ${JSON.stringify(data).substring(0, 100)}...`);
      
      // Update session ID if provided
      if (data.sessionId) {
        widgetState.sessionId = data.sessionId;
        debugLog(`Session ID updated: ${data.sessionId}`);
      }
      
      // Add bot response to chat
      addMessage('bot', data.response, data.sources);
      
    } catch (error) {
      debugLog(`Error sending message: ${error.message}`, 'error');
      addMessage('bot', 'Sorry, I encountered an error. Please try again later.');
    } finally {
      hideLoading();
    }
  }
  
  // Setup all event listeners
  function setupEventListeners() {
    debugLog('Setting up event listeners');
    
    try {
      // Toggle widget on button click
      const toggleBtn = document.getElementById('chatsphere-widget-button');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleWidget);
        debugLog('Toggle button listener added');
      } else {
        debugLog('Toggle button not found', 'error');
      }
      
      // Close widget
      const closeBtn = document.getElementById('chatsphere-widget-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleWidget();
        });
        debugLog('Close button listener added');
      } else {
        debugLog('Close button not found', 'error');
      }
      
      // Input handling
      const inputEl = document.getElementById('chatsphere-widget-input');
      if (inputEl) {
        inputEl.addEventListener('input', (e) => {
          widgetState.inputValue = e.target.value;
        });
        
        inputEl.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            sendMessage(widgetState.inputValue);
          }
        });
        debugLog('Input field listeners added');
      } else {
        debugLog('Input field not found', 'error');
      }
      
      // Send button
      const sendBtn = document.getElementById('chatsphere-widget-send');
      if (sendBtn) {
        sendBtn.addEventListener('click', () => {
          sendMessage(widgetState.inputValue);
        });
        debugLog('Send button listener added');
      } else {
        debugLog('Send button not found', 'error');
      }
    } catch (e) {
      debugLog(`Error setting up event listeners: ${e.message}`, 'error');
    }
  }
  
  // Initialize widget with configuration
  async function initWidget() {
    debugLog('Initializing widget');
    
    try {
      // Add styles first
      addStyles();
      
      // Fetch widget configuration from API
      const configEndpoint = `/api/chatbots/widget-config/${chatbotId}`;
      const configUrl = `${apiBase}${configEndpoint}`;
      
      debugLog(`Fetching config from ${configUrl}`);
      const response = await fetch(configUrl);
      
      if (!response.ok) {
        const errorText = await response.text();
        debugLog(`Config API error (${response.status}): ${errorText}`, 'error');
        throw new Error(`Failed to fetch chatbot configuration: ${response.status}`);
      }
      
      const config = await response.json();
      debugLog(`Received config: ${JSON.stringify(config)}`);
      
      // Extract appearance settings
      const appearance = config.settings?.appearance || {};
      
      // Prepare configuration with fallbacks
      const widgetConfig = {
        chatbotId: chatbotId,
        position: appearance.position || defaultPosition,
        primaryColor: appearance.primaryColor || defaultPrimaryColor,
        secondaryColor: appearance.secondaryColor || '#f3f4f6',
        title: appearance.chatTitle || config.name || defaultTitle,
        showBranding: appearance.showBranding !== false && showBranding,
        initialMessage: appearance.initialMessage || 'Hi! How can I help you today?'
      };
      
      debugLog(`Final widget config: ${JSON.stringify(widgetConfig)}`);
      
      // Create widget elements
      createWidget(widgetConfig);
      
      // Setup event listeners
      setupEventListeners();
      
      // Mark as initialized
      widgetState.initialized = true;
      debugLog('Widget initialization complete', 'info');
      
    } catch (e) {
      debugLog(`Error initializing widget: ${e.message}`, 'error');
      // Show error notification
      const errorNotification = document.createElement('div');
      errorNotification.className = 'chatsphere-widget-error';
      errorNotification.innerHTML = `
        <p>Failed to initialize chat widget</p>
        <p class="error-details">${e.message}</p>
      `;
      document.body.appendChild(errorNotification);
      setTimeout(() => {
        if (errorNotification.parentNode) {
          document.body.removeChild(errorNotification);
        }
      }, 5000);
    }
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    debugLog('Document is still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    debugLog('Document is ready, initializing immediately');
    initWidget();
  }
})(); 