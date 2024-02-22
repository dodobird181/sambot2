
let chatContainer = null;
let userInputBox = null;


/**
 * Stuff to happen after the DOM fully-loads.
 */
const onDomLoad = () => {
    chatContainer = document.getElementById('stream-container');
    userInputBox = document.getElementById('input-box');
    userInputBox.addEventListener('keypress', onKeyPress);
    loadMessages(chatContainer)
        .then(_ => document.body.style.display = "block")
        .then(_ => scrollDown())
        .then(_ => {
            if (0 == numChatMessages()){
                const initialPrompt = 'Lorem Ipsum';
                const initialStream = new EventSource('/stream_initial?user_content=' + initialPrompt);
                streamMessageData(initialStream);
            }
        });
};

/**
 * Return the number of chat messages in the ordered list.
 */
const numChatMessages = () => {
    return chatContainer.querySelectorAll('li').length;
};

/**
 * Load Sambot messages into a DOM element. Messages are represented by <li> tags.
 * @param {*} container the DOM element to load HTML messages into.
 */
const loadMessages = (container) => {
    return fetch('/checkin', {method: 'GET'})
    .then(response => response.text())
    .then(htmlText => container.innerHTML = htmlText)
    .catch(error => console.error('Failed to load messages.', error));
};

/**
 * Disable a DOM element.
 */
const disableElement = (element) => {
    element.setAttribute('disabled', 'true');
};

/**
 * Enable a DOM element.
 */
const enableElement = (element) => {
    element.removeAttribute('disabled');
};

/**
 * Get text from the user input box and clear it afterwards.
 */
const consumeUserInput = () => {
    const input = encodeURIComponent(userInputBox.value);
    userInputBox.value = '';
    return input;
};

/**
 * Scroll to the bottom of the messages display.
 */
const scrollDown = () => {
    chatContainer.scrollTop = chatContainer.scrollHeight;
};

/**
 * Disable scrolling on chat container.
 */
const disableChatScrolling = () => {
    chatContainer.style.overflowY = 'hidden'
};

/**
 * Enable scrolling on chat container.
 */
const enableChatScrolling = () => {
    chatContainer.style.overflowY = ''
};

/**
 * Start the ellipsis animation at the bottom of the chat container.
 * This will be automatically overridden when sambot starts streaming data.
 */
const startEllipsisAnim = () => {
    chatContainer.innerHTML += '<li id="ellipsis" class="assistant"></li>'
    const ellipsisElement = document.getElementById('ellipsis');
    let dots = 0;
    return setInterval(() => {
        dots = (dots + 1) % 4;
        ellipsisElement.textContent = '.'.repeat(dots) + '\u200B';
        scrollDown();
    }, 500);
};

const streamMessageData = (stream) => {
    let ellipsisInterval = null; // populated by startEllipsisAnim()
    disableElement(userInputBox);
    disableChatScrolling();
    stream.onmessage = (event) => {
        if (event.data === 'STOP'){
            stream.close();
            enableElement(userInputBox);
            enableChatScrolling();
            userInputBox.focus();
        } else if (event.data === 'START ELLIPSIS'){
            ellipsisInterval = startEllipsisAnim();
        } else {
            clearInterval(ellipsisInterval);
            chatContainer.innerHTML = event.data;
            scrollDown();
        }
    };
};

/**
 * Handle global (docuent-level) keypress events.
 */
const onKeyPress = (keyPressEvent) => {
    if (keyPressEvent.key === 'Enter') {
        keyPressEvent.preventDefault(); // prevent default form-submission behaviour
        const userInput = consumeUserInput();
        const sambotStream = new EventSource('/stream?user_content=' + userInput);
        streamMessageData(sambotStream);
    }
};

// Listen for when the DOM has fully-loaded.
document.addEventListener('DOMContentLoaded', onDomLoad);