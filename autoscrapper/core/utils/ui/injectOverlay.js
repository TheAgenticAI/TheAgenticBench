let awaitingUserResponse = false;
let show_details = true;

function injectOveralyStyles() {
    let style = document.createElement("style");
    style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    ::-webkit-scrollbar {
      width: 6px;
      border: solid 3px transparent;
    }

    ::-webkit-scrollbar-track {
      background-color: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background-color: rgba(147, 51, 234, 0.3);
      border-radius: 6px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background-color: rgba(147, 51, 234, 0.5);
    }

    .tawebagent-ui-automation-highlight {
      border-width: 2px !important;
      border-style: solid !important;
      animation: automation_highlight_fadeout_animation 5s linear 1 forwards !important;
    }

    @keyframes automation_highlight_fadeout_animation {
      0% { border-color: rgba(147, 51, 234, 1); }
      50% { border-color: rgba(147, 51, 234, 1); }
      100% { border-color: rgba(147, 51, 234, 0); }
    }

    .tawebagent-processing {
      background: linear-gradient(135deg, #4F46E5, #9333EA);
      animation: tawebagent-gradient-shift 3s ease infinite;
    }

    @keyframes tawebagent-gradient-shift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .tawebagent-init {
      background: #F3F4F6;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .tawebagent-done {
      background: linear-gradient(135deg, #059669, #10B981);
    }

    .tawebagent-collapsed {
      cursor: pointer;
      width: 64px;
      height: 64px;
      border-radius: 50%;
      position: fixed;
      right: 24px;
      bottom: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      background: white;
      z-index: 2147483646;
    }

    .tawebagent-collapsed:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    .tawebagent-chat-container {
  margin: 0;
  width: 380px;
  height: 600px;
  position: fixed;
  display: flex;
  flex-direction: column;
  right: 24px;
  bottom: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 2147483646;
}

  #tawebagent-chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100% - 240px); /* Explicit height calculation */
  min-height: 200px; /* Minimum height */
  margin: 0;
  background: white;
}



  .tawebagent-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
  height: 64px; /* Fixed height */
  min-height: 64px; /* Prevent compression */
}

    .tawebagent-logo-container {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .tawebagent-logo {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #4F46E5, #9333EA);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .tawebagent-logo-inner {
      width: 24px;
      height: 24px;
      background: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .tawebagent-logo-core {
      width: 16px;
      height: 16px;
      background: linear-gradient(135deg, #4F46E5, #9333EA);
      border-radius: 50%;
    }

    .tawebagent-title {
      font-family: 'Inter', sans-serif;
      font-weight: 600;
      font-size: 16px;
      color: #1F2937;
    }

   .tawebagent-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0; /* This is crucial for proper scrolling */
  max-height: calc(100% - 180px); /* Adjust based on header + input + settings height */
}

    .tawebagent-message {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 12px;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      line-height: 1.5;
    }

    .tawebagent-user-message {
      align-self: flex-end;
      background: linear-gradient(135deg, #4F46E5, #9333EA);
      color: white;
    }

    .tawebagent-system-message {
      align-self: flex-start;
      background: #F3F4F6;
      color: #1F2937;
    }

   .tawebagent-input-container {
  padding: 16px;
  background: white;
  border-top: 1px solid #E5E7EB;
  margin-bottom: 65px; /* Add space for disclaimer */
  z-index: 2;

}

    .tawebagent-input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 8px;
}

  .tawebagent-textarea {
  width: 100%;
  max-height: 75px; /* Limit maximum height */
  min-height: 50px;
  padding: 4px;
  border: none;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  resize: none;
  transition: all 0.2s ease;
  background: transparent;
  margin-bottom: 0; /* Remove bottom margin */
}

    .tawebagent-textarea:focus {
      outline: none;
      
    }

    .tawebagent-send-button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  margin-top: auto;
  margin-bottom: 4px;
}

    .tawebagent-send-button-enabled {
      background: linear-gradient(135deg, #4F46E5, #9333EA);
      color: white;
    }

    .tawebagent-send-button-disabled {
      background: #F3F4F6;
      color: #9CA3AF;
    }

    .tawebagent-settings-bar {
  padding: 12px 16px;
  height: 48px;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #E5E7EB;
  background: white;
}

.tawebagent-overlay-wrapper {
  position: fixed;
  right: 24px;
  bottom: 24px;
  pointer-events: none;
  z-index: 2147483646;
}

.tawebagent-overlay-wrapper > * {
  pointer-events: auto;
}

    .tawebagent-toggle-container {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tawebagent-toggle {
      position: relative;
      width: 36px;
      height: 20px;
      background: #E5E7EB;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .tawebagent-toggle-checked {
      background: #9333EA;
    }

    .tawebagent-toggle-thumb {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 16px;
      height: 16px;
      background: white;
      border-radius: 50%;
      transition: all 0.2s ease;
    }

    .tawebagent-toggle-checked .tawebagent-toggle-thumb {
      left: 18px;
    }

   .tawebagent-disclaimer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: #F9FAFB;
  border-top: 1px solid #E5E7EB;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  color: #6B7280;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 3; /* Ensure it stays on top */
  height: 40px;
}
  `;
    document.head.appendChild(style);
}

function showCollapsedOverlay(processing_state = "processing") {
    removeOverlay();
    window.overlay_state_changed(true);

    // Create wrapper
    const wrapper = document.createElement("div");
    wrapper.id = "tawebagent-overlay-wrapper";
    wrapper.className = "tawebagent-overlay-wrapper";

    // Create main container
    const collapsed = document.createElement("div");
    collapsed.id = "tawebagent-overlay";
    collapsed.classList.add("tawebagent-collapsed");

    // Create gradient background wrapper
    const gradientWrapper = document.createElement("div");
    gradientWrapper.style.width = "48px";
    gradientWrapper.style.height = "48px";
    gradientWrapper.style.background = "linear-gradient(135deg, #4F46E5, #9333EA)";
    gradientWrapper.style.borderRadius = "50%";
    gradientWrapper.style.display = "flex";
    gradientWrapper.style.alignItems = "center";
    gradientWrapper.style.justifyContent = "center";

    // Create white circle
    const whiteCircle = document.createElement("div");
    whiteCircle.style.width = "40px";
    whiteCircle.style.height = "40px";
    whiteCircle.style.background = "white";
    whiteCircle.style.borderRadius = "50%";
    whiteCircle.style.display = "flex";
    whiteCircle.style.alignItems = "center";
    whiteCircle.style.justifyContent = "center";

    // Create inner gradient circle
    const innerCircle = document.createElement("div");
    innerCircle.style.width = "32px";
    innerCircle.style.height = "32px";
    innerCircle.style.background = "linear-gradient(135deg, #4F46E5, #9333EA)";
    innerCircle.style.borderRadius = "50%";

    // Assembly
    whiteCircle.appendChild(innerCircle);
    gradientWrapper.appendChild(whiteCircle);
    collapsed.appendChild(gradientWrapper);

    // Add state-based styling
    updateOverlayState(processing_state, true);

    // Add event listeners
    collapsed.addEventListener("mouseover", () => {
        collapsed.style.transform = "scale(1.05)";
    });

    collapsed.addEventListener("mouseout", () => {
        collapsed.style.transform = "scale(1)";
    });

    collapsed.addEventListener("click", () => {
        const state = document.getElementById("tawebagent-overlay").querySelector(".tawebagent-processing") ? "processing" :
            document.getElementById("tawebagent-overlay").querySelector(".tawebagent-done") ? "done" : "init";
        showExpandedOverlay(state, show_details);
    });

    wrapper.appendChild(collapsed);
    document.body.appendChild(wrapper);
}

function updateOverlayState(processing_state, is_collapsed) {
    const element = is_collapsed ?
        document.getElementById("tawebagent-overlay") :
        document.getElementById("tawebagentExpandedAnimation");

    if (!element) return;

    // Remove all state classes
    element.classList.remove("tawebagent-init", "tawebagent-processing", "tawebagent-done",
        "tawebagent-initStateLine", "tawebagent-processingLine", "tawebagent-doneStateLine");

    if (is_collapsed) {
        switch (processing_state) {
            case "init":
                element.classList.add("tawebagent-init");
                enableOverlay();
                break;
            case "processing":
                element.classList.add("tawebagent-processing");
                disableOverlay();
                break;
            case "done":
                element.classList.add("tawebagent-done");
                enableOverlay();
                break;
        }
    } else {
        switch (processing_state) {
            case "init":
                element.classList.add("tawebagent-initStateLine");
                enableOverlay();
                break;
            case "processing":
                element.classList.add("tawebagent-processingLine");
                disableOverlay();
                break;
            case "done":
                element.classList.add("tawebagent-doneStateLine");
                enableOverlay();
                break;
        }
    }
}

function createSvgIcon(type) {
    const icons = {
        send: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2"/>
          </svg>`,
        close: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
             <path d="M18 6L6 18M6 6l12 12"/>
           </svg>`,
        minimize: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
              </svg>`,
        alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
             <circle cx="12" cy="12" r="10"/>
             <line x1="12" y1="8" x2="12" y2="12"/>
             <line x1="12" y1="16" x2="12.01" y2="16"/>
           </svg>`
    };

    const wrapper = document.createElement("div");
    wrapper.innerHTML = icons[type] || "";
    return wrapper.firstChild;
}

function removeOverlay() {
    const wrapper = document.getElementById("tawebagent-overlay-wrapper");
    if (wrapper) {
        wrapper.remove();
    }
}

function enableOverlay() {
    const input = document.getElementById("tawebagent-user-input");
    if (input) {
        input.placeholder = "What can I help you solve today?";
        input.disabled = false;
    }
}

function disableOverlay() {
    const input = document.getElementById("tawebagent-user-input");
    if (input) {
        input.placeholder = "Processing...";
        input.disabled = true;
    }
}

function isDisabled() {
    const input = document.getElementById("tawebagent-user-input");
    return input ? input.disabled : true;
}

function showExpandedOverlay(processing_state = "init", show_steps = true) {
    removeOverlay();
    window.overlay_state_changed(false);
    show_details = show_steps;

    // Create wrapper
    const wrapper = document.createElement("div");
    wrapper.id = "tawebagent-overlay-wrapper";
    wrapper.className = "tawebagent-overlay-wrapper";

    // Create main container
    const expandedOverlay = document.createElement("div");
    expandedOverlay.id = "tawebagent-overlay";
    expandedOverlay.className = "tawebagent-chat-container";
    expandedOverlay.style.position = "fixed";
    expandedOverlay.style.right = "24px";
    expandedOverlay.style.bottom = "24px";

    // Create header
    const header = createHeader();

    // Create progress bar
    const progressBar = document.createElement("div");
    progressBar.id = "tawebagentExpandedAnimation";
    progressBar.style.height = "2px";
    progressBar.style.width = "100%";

    // Create messages container
    const messagesContainer = document.createElement("div");
    messagesContainer.id = "tawebagent-chat-box";
    messagesContainer.className = "tawebagent-chat-messages";

    // Create settings bar
    const settingsBar = createSettingsBar();

    // Create input section
    const inputSection = createInputSection();

    // Create disclaimer
    const disclaimer = createDisclaimer();

    // Assembly
    expandedOverlay.appendChild(header);
    expandedOverlay.appendChild(progressBar);
    expandedOverlay.appendChild(messagesContainer);
    expandedOverlay.appendChild(settingsBar);
    expandedOverlay.appendChild(inputSection);
    expandedOverlay.appendChild(disclaimer);

    wrapper.appendChild(expandedOverlay);
    document.body.appendChild(wrapper);
    updateOverlayState(processing_state, false);
    setupEventListeners();
    setupScrollCheck();
    focusOnOverlayInput();

    setInterval(maintainScroll, 100);
}

function createHeader() {
    const header = document.createElement("div");
    header.className = "tawebagent-chat-header";

    const logoContainer = document.createElement("div");
    logoContainer.className = "tawebagent-logo-container";

    // Create logo
    const logo = document.createElement("div");
    logo.className = "tawebagent-logo";
    const logoInner = document.createElement("div");
    logoInner.className = "tawebagent-logo-inner";
    const logoCore = document.createElement("div");
    logoCore.className = "tawebagent-logo-core";
    logoInner.appendChild(logoCore);
    logo.appendChild(logoInner);

    const title = document.createElement("span");
    title.className = "tawebagent-title";
    title.textContent = "AutoScraper";

    logoContainer.appendChild(logo);
    logoContainer.appendChild(title);

    const closeButton = document.createElement("button");
    closeButton.innerHTML = createSvgIcon("minimize").outerHTML;
    closeButton.className = "tawebagent-send-button";
    closeButton.style.position = "static";
    closeButton.onclick = () => {
        const currentState = document.getElementById("tawebagentExpandedAnimation").className;
        const state = currentState.includes("processingLine") ? "processing" :
            currentState.includes("doneStateLine") ? "done" : "init";
        showCollapsedOverlay(state, show_details);
    };

    header.appendChild(logoContainer);
    header.appendChild(closeButton);
    return header;
}

function createSettingsBar() {
    const settingsBar = document.createElement("div");
    settingsBar.className = "tawebagent-settings-bar";

    const toggleContainer = document.createElement("div");
    toggleContainer.className = "tawebagent-toggle-container";

    const label = document.createElement("span");
    label.textContent = "Show Details";
    label.style.color = "#6B7280";
    label.style.fontSize = "14px";

    const toggle = document.createElement("div");
    toggle.className = `tawebagent-toggle ${show_details ? 'tawebagent-toggle-checked' : ''}`;
    const thumb = document.createElement("div");
    thumb.className = "tawebagent-toggle-thumb";
    toggle.appendChild(thumb);

    toggle.onclick = () => {
        show_details = !show_details;
        toggle.classList.toggle("tawebagent-toggle-checked");

        // Update messages visibility without clearing them
        const chatBox = document.getElementById("tawebagent-chat-box");
        if (chatBox) {
            const messages = chatBox.getElementsByTagName('div');
            Array.from(messages).forEach(msg => {
                if (msg.getAttribute('data-message-type') === 'step') {
                    msg.style.display = show_details ? 'flex' : 'none';
                }
            });

            // Ensure proper scroll position after toggle
            setTimeout(() => {
                chatBox.scrollTop = chatBox.scrollHeight;
            }, 100);
        }

        window.show_steps_state_changed(show_details);
    };

    toggleContainer.appendChild(label);
    toggleContainer.appendChild(toggle);
    settingsBar.appendChild(toggleContainer);

    return settingsBar;
}

function createInputSection() {
    const inputContainer = document.createElement("div");
    inputContainer.className = "tawebagent-input-container";

    const inputWrapper = document.createElement("div");
    inputWrapper.className = "tawebagent-input-wrapper";

    const textarea = document.createElement("textarea");
    textarea.id = "tawebagent-user-input";
    textarea.className = "tawebagent-textarea";
    textarea.placeholder = "What can I help you solve today?";
    textarea.rows = 1; // Changed from 3 to 1 for better initial height

    const sendButton = document.createElement("button");
    sendButton.id = "tawebagent-send-btn";
    sendButton.className = "tawebagent-send-button tawebagent-send-button-disabled";
    sendButton.innerHTML = createSvgIcon("send").outerHTML;
    sendButton.type = "button"; // Add this to prevent form submission

    inputWrapper.appendChild(textarea);
    inputWrapper.appendChild(sendButton);
    inputContainer.appendChild(inputWrapper);

    // Add auto-resize functionality
    textarea.addEventListener('input', function () {
        // Reset height temporarily to get the correct scrollHeight
        this.style.height = 'auto';
        // Set new height
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });

    return inputContainer;
}

function createDisclaimer() {
    const disclaimer = document.createElement("div");
    disclaimer.className = "tawebagent-disclaimer";

    const icon = createSvgIcon("alert");
    const text = document.createElement("span");
    text.textContent = "AutoScraper may make mistakes. Verify key info.";

    disclaimer.appendChild(icon);
    disclaimer.appendChild(text);

    return disclaimer;
}

function setupEventListeners() {
    const textarea = document.getElementById("tawebagent-user-input");
    const sendButton = document.getElementById("tawebagent-send-btn");

    textarea.addEventListener("input", (e) => {
        const hasText = e.target.value.trim().length > 0;
        sendButton.className = `tawebagent-send-button ${hasText ? 'tawebagent-send-button-enabled' : 'tawebagent-send-button-disabled'}`;
    });

    textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });

    sendButton.addEventListener("click", () => {
        const text = textarea.value.trim();
        if (text && !isDisabled()) {
            if (awaitingUserResponse) {
                addUserMessage(text);
                textarea.value = "";
            } else {
                clearOverlayMessages();
                addUserMessage(text);
                disableOverlay();
                window.process_task(text);
                textarea.value = "";
            }
            sendButton.className = "tawebagent-send-button tawebagent-send-button-disabled";
        }
    });
}

function addMessage(message, sender, message_type = "plan") {
    const chatBox = document.getElementById("tawebagent-chat-box");
    if (!chatBox) return;

    // Create message container with proper styling
    const messageContainer = document.createElement("div");
    messageContainer.style.width = "100%";
    messageContainer.style.display = "flex";
    messageContainer.style.justifyContent = sender === "user" ? "flex-end" : "flex-start";
    messageContainer.style.minHeight = "min-content";
    messageContainer.setAttribute('data-message-type', message_type); // Add this for tracking

    // Create message bubble
    const messageBubble = document.createElement("div");
    messageBubble.className = `tawebagent-message ${sender === "user" ? "tawebagent-user-message" : "tawebagent-system-message"
        }`;

    // Parse message content
    let parsedMessage = message;
    try {
        parsedMessage = JSON.parse(message);
    } catch (e) {
        // Keep original message if parsing fails
    }
    messageBubble.textContent = parsedMessage;

    messageContainer.appendChild(messageBubble);
    chatBox.appendChild(messageContainer);

    // Ensure proper scrolling
    setTimeout(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 100);
}

function setupScrollCheck() {
    const chatBox = document.getElementById("tawebagent-chat-box");
    if (!chatBox) return;

    // Force recalculation of scroll heights
    function refreshScroll() {
        chatBox.style.display = 'none';
        chatBox.offsetHeight; // Force reflow
        chatBox.style.display = 'flex';

        const lastMessage = chatBox.lastElementChild;
        if (lastMessage) {
            lastMessage.scrollIntoView({
                behavior: "auto",
                block: "end",
                inline: "nearest"
            });
        }
    }

    // Initial refresh
    setTimeout(refreshScroll, 100);

    // Periodic check for first few seconds
    let checks = 0;
    const interval = setInterval(() => {
        refreshScroll();
        checks++;
        if (checks >= 5) clearInterval(interval);
    }, 1000);
}

function addSystemMessage(message, is_awaiting_user_response = false, message_type = "plan") {
    awaitingUserResponse = is_awaiting_user_response;

    // Add loading indicator if processing
    if (message_type === "processing") {
        addLoadingIndicator();
    }

    requestAnimationFrame(() => {
        addMessage(message, "system", message_type);
    });
}

function addLoadingIndicator() {
    const chatBox = document.getElementById("tawebagent-chat-box");
    if (!chatBox) return;

    const loadingContainer = document.createElement("div");
    loadingContainer.className = "tawebagent-message tawebagent-system-message";
    loadingContainer.style.display = "flex";
    loadingContainer.style.gap = "4px";
    loadingContainer.style.padding = "8px 16px";

    // Create bouncing dots
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.style.width = "8px";
        dot.style.height = "8px";
        dot.style.borderRadius = "50%";
        dot.style.background = "#9333EA";
        dot.style.animation = "bounce 1.4s infinite ease-in-out";
        dot.style.animationDelay = `${i * 0.16}s`;
        loadingContainer.appendChild(dot);
    }

    chatBox.appendChild(loadingContainer);
}

function addUserMessage(message) {
    requestAnimationFrame(() => {
        addMessage(message, "user");
    });
}

function clearOverlayMessages() {
    const chatBox = document.getElementById("tawebagent-chat-box");
    if (!chatBox) return;

    while (chatBox.firstChild) {
        chatBox.removeChild(chatBox.firstChild);
    }
}

function focusOnOverlayInput() {
    const input = document.getElementById("tawebagent-user-input");
    if (input) {
        requestAnimationFrame(() => {
            input.focus();
        });
    }
}

function maintainScroll() {
    const chatBox = document.getElementById("tawebagent-chat-box");
    if (!chatBox) return;

    const shouldScroll = chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 1;

    if (shouldScroll) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Add these keyframe animations to the existing styles
function addKeyframeAnimations() {
    const style = document.createElement("style");
    style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeOut {
      from { opacity: 1; transform: translateY(0); }
      to { opacity: 0; transform: translateY(-10px); }
    }

    @keyframes bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }

    @keyframes gradient {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
  `;
    document.head.appendChild(style);
}

// Initialize
function init() {
    injectOveralyStyles();
    addKeyframeAnimations();
    // Start with collapsed view
    showCollapsedOverlay("init");
}

// Call initialization
init();