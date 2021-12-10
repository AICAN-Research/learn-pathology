// Global variables

// Functions
function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.className = themeName;
}

// Immediately invoked function to set the theme on initial load
(function () {
    setTheme('theme_default')
})();
