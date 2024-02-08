
// load old conversation on page load, if one exists!
const container = document.getElementById('stream-container');
fetch('/checkin', {method: 'GET'})
.then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    // or response.json() if the API returns JSON
    return response.text();
})
.then(data => {
    container.innerHTML = data;
})
.catch(error => {
    console.error('There was a problem with your fetch operation:', error);
});

document.addEventListener('DOMContentLoaded', function() {
    var inputBox = document.getElementById('input-box');
    inputBox.addEventListener('keypress', function(event) {
        // Check if the key pressed is the Enter key
        if (event.key === 'Enter') {
            // Prevent the default action to avoid submitting a form if the input is part of one
            event.preventDefault();

            // TODO: All of this is DOGWATER... shouldn't actually post this up long-term
            // without separating out the JS and CCSS into their own files like a normal human.

            inputBox.setAttribute('disabled', 'true');
            let ellipsisInterval = null;

            // Grab the text and encode
            var user_content = encodeURIComponent(inputBox.value);
            inputBox.value = '';

            // scroll to bottom and lock scrolling until response is finished
            const container = document.getElementById('stream-container');
            container.scrollTop = container.scrollHeight;
            document.body.style.overflowY = '';

            // Do something with the text, e.g., log it to the console
            const eventSource = new EventSource('/stream?user_content=' + user_content);
            eventSource.onmessage = function(event) {
                if (event.data === 'STOP'){
                    eventSource.close();
                    inputBox.removeAttribute('disabled');
                    document.body.style.overflowY = 'auto';
                }

                else if (event.data === 'START ELLIPSIS'){
                    container.innerHTML += '<li id="ellipsis" class="assistant"></li>'
                    const ellipsisElement = document.getElementById('ellipsis');
                    let dots = 0;
                    let ellipsisInterval = setInterval(() => {
                        dots = (dots + 1) % 4;
                        ellipsisElement.textContent = '.'.repeat(dots) + '\u200B';
                        container.scrollTop = container.scrollHeight;
                    }, 500);
                }

                else {
                    clearInterval(ellipsisInterval);
                    container.innerHTML = event.data;
                    container.scrollTop = container.scrollHeight;
                }
            };
        }
    });
});