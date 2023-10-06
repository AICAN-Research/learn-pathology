// Global variables

// Functions
function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.className = themeName;
}

function setBackground(colorHex) {
    var bodyStyles = document.body.style;
    console.log(bodyStyles);
    bodyStyles.setProperty('--background', colorHex);
}

// Immediately invoked function to set the theme on initial load
(function () {
    setTheme('theme_default')
})();


// Toggle or collapse sidebar/menu bar
function toggleSidebar() {
    $('#sidebar').toggleClass('active');
}

function collapseSidebar() {
    $('#sidebar').addClass('active');
}
