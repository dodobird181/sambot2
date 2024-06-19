

document.addEventListener("DOMContentLoaded", () => {

    const inputBox = document.getElementById('inputBox');
    const textWidthCalculator = document.getElementById('textWidthCalculator');
    const pills = document.querySelectorAll('.pill');
    const messagesContainer = document.getElementById('messagesContainer');

    // grow input box when text added
    inputBox.addEventListener('input', function() {
        textWidthCalculator.textContent = this.value;
        const width = textWidthCalculator.offsetWidth;
        this.style.width = (width + 20) + 'px';
    });

    // submit when pill clicked
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            inputBox.value = pill.textContent;
            inputBox.dispatchEvent(new Event('input'));
            // TODO submit here once submission is built
        });
    });

    // submit when enter pressed
    inputBox.addEventListener('keypressed', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default Enter key behavior
            submitUserInput();
        }
    });

    // submit logic
    function submitUserInput() {
        alert(`You submitted: ${userContent}`);
        inputBox.value = ''; // Clear the input field

        const source = new EventSource('/submit?user_content=' + inputBox.value);
        source.onmessage = function(event) {
            if (event.data === 'STOP'){
                stream.close();
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