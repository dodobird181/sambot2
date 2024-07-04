

document.addEventListener("DOMContentLoaded", () => {

    const inputBox = document.getElementById('inputBox');
    const textWidthCalculator = document.getElementById('textWidthCalculator');
    const pills = document.querySelectorAll('.pill');
    const messagesContainer = document.getElementById('messagesContainer');

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
                source.close();
            } else {
                const parser = new DOMParser();
                const doc = parser.parseFromString(event.data, 'text/html');
                const newContent = doc.body.innerHTML;  // assumes stream data wrapped in body
                messagesContainer.innerHTML = newContent;
            }
        };
        source.onerror = function(event) {
            console.error("Error occurred in the EventSource stream:", event);
            source.close();
        };
    }

});