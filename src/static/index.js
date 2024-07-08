

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
            if (!pill.classList.contains('pill-disabled')){
                inputBox.value = pill.textContent;
                inputBox.dispatchEvent(new Event('input'));
                submitUserInput();
                inputBox.dispatchEvent(new Event('input'));
            }
        });
    });

    // submit when enter pressed
    inputBox.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default Enter key behavior
            if (!submitButton.disabled){
                submitUserInput();
            }
        }
    });

    // submit logic
    function submitUserInput() {
        const userContent = inputBox.value;
        inputBox.value = ''; // Clear the input field

        disableSubmission();

        const source = new EventSource('/submit?user_content=' + userContent);
        source.onmessage = function(event) {
            if (event.data === 'STOP'){
                location.reload(true);  // reload the page to generate pills... TODO: this is a hack
                scrollToBottom();
                source.close();
                enableSubmission();
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
            enableSubmission();
        };
    }

    function disableSubmission() {
        inputBox.disabled = true;
        inputBox.classList.add('submit-button-disabled');
        submitButton.disabled = true;
        submitButton.classList.add('submit-button-disabled');
        pills.forEach(pill => {
            pill.classList.add('pill-disabled');
        });
    }

    function enableSubmission() {
        inputBox.disabled = false;
        inputBox.classList.remove('submit-button-disabled');
        submitButton.disabled = false;
        submitButton.classList.remove('submit-button-disabled');
        pills.forEach(pill => {
            pill.disabled = false;
            pill.classList.remove('pill-disabled');
        });
    }

    function scrollToBottom() {
        const messagesContainerEl = document.getElementById('messagesContainer');
        messagesContainerEl.scrollTop = messagesContainerEl.scrollHeight;
    }

    scrollToBottom();

});