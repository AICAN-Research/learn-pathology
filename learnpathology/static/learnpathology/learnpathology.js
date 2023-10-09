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
    if ($('#sidebar').hasClass('active')) {
        expandSidebar();
    } else {
        collapseSidebar();
    }
}

function collapseSidebar() {
    $('#sidebar').addClass('active');
    // Adjust margin/location of other content
    document.getElementById('content').style['margin-left'] = 'var(--sidebar-width-collapsed)';
}

function expandSidebar() {
    $('#sidebar').removeClass('active');
    // Adjust margin/location of other content
    document.getElementById('content').style['margin-left'] = 'var(--sidebar-width)';
}
