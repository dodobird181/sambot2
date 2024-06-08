

document.addEventListener("DOMContentLoaded", () => {
    const growingInputs = document.getElementsByClassName('growing-input');
    const textWidthCalculator = document.getElementById('text-width-calculator');
    for (let i = 0; i < growingInputs.length; i++) {
        growingInputs[i].addEventListener('input', function() {
            textWidthCalculator.textContent = this.value;
            const width = textWidthCalculator.offsetWidth;
            this.style.width = (width + 20) + 'px'; // Add some padding to avoid too tight fit
        });
    }
});