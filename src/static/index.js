

document.addEventListener("DOMContentLoaded", () => {

    const inputBox = document.getElementById('inputBox');
    const textWidthCalculator = document.getElementById('textWidthCalculator');
    const pills = document.querySelectorAll('.pill');

    // grow input box when text added
    inputBox.addEventListener('input', function() {
        textWidthCalculator.textContent = this.value;
        const width = textWidthCalculator.offsetWidth;
        this.style.width = (width + 20) + 'px';
    });

    // submit response on pill click
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            inputBox.value = pill.textContent;
            inputBox.dispatchEvent(new Event('input'));
            // TODO submit here once submission is built
        });
    });


});