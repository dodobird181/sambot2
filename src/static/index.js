

document.addEventListener("DOMContentLoaded", () => {

    const inputBox = document.getElementById('inputBox');
    const textWidthCalculator = document.getElementById('textWidthCalculator');
    const pills = document.querySelectorAll('.pill');
    const messagesContainer = document.getElementById('messagesContainer');
    const submitButton = document.getElementById("submitButton");
    const copyright = document.getElementById("copyright");

    const year = new Date().getFullYear();
    copyright.innerHTML = "Copyright " + year + " Samuel Morris";

    // make submit button work
    submitButton.addEventListener('click', function() {
        submitUserInput();
    });

    // grow input box when text added
    inputBox.addEventListener('input', function() {
        textWidthCalculator.textContent = this.value;
        const width = textWidthCalculator.offsetWidth;
        this.style.width = (width + 30) + 'px';
    });

    // submit when pill clicked
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            inputBox.value = pill.textContent;
            inputBox.dispatchEvent(new Event('input'));
            submitUserInput();
            inputBox.dispatchEvent(new Event('input'));
        });
    });

    // submit when enter pressed
    inputBox.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default Enter key behavior
            submitUserInput();
        }
    });

    // submit logic
    function submitUserInput() {
        const userContent = inputBox.value;
        inputBox.value = ''; // Clear the input field

        const source = new EventSource('/submit?user_content=' + userContent);
        source.onmessage = function(event) {
            if (event.data === 'STOP'){
                location.reload(true);  // reload the page to generate pills... TODO: this is a hack
                scrollToBottom();
                source.close();
            } else {
                const parser = new DOMParser();
                const doc = parser.parseFromString(event.data, 'text/html');
                const newContent = doc.body.innerHTML;  // assumes stream data wrapped in body
                messagesContainer.innerHTML = newContent;
                scrollToBottom();
            }
        };
        source.onerror = function(event) {
            console.error("Error occurred in the EventSource stream:", event);
            source.close();
        };
    }

    function scrollToBottom() {
        const messagesContainerEl = document.getElementById('messagesContainer');
        messagesContainerEl.scrollTop = messagesContainerEl.scrollHeight;
    }

    scrollToBottom();

});