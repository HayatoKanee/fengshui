document.addEventListener('DOMContentLoaded', function () {
    const langLinks = document.querySelectorAll('[data-lang-switch]');

    langLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent the default link behavior
            const selectedLang = this.getAttribute('data-lang-switch');
            switchLanguage(selectedLang);
        });
    });
});

function switchLanguage(lang) {
    const allContent = document.querySelectorAll('.lang');
    allContent.forEach(content => {
        if (content.getAttribute('data-lang') === lang) {
            content.style.display = 'block';
        } else {
            content.style.display = 'none';
        }
    });
    const langLinks = document.querySelectorAll('[data-lang-switch]');
    langLinks.forEach(link => {
        if (link.getAttribute('data-lang-switch') === lang) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}