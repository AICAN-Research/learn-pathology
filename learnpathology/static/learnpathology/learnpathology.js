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


function highlightMenuItem() {
    let menu_item = '';
    if (location.href.includes('slide')){
        menu_item = 'slide';
    } else if (location.href.includes('course')) {
        menu_item = 'course';
    } else if (location.href.includes('task/list')) {
        menu_item = 'task';
    } else if (location.href.includes('tag/')) {
        menu_item = 'tag';
    } else {
        return;
    }
    /* TODO: Check menu options that no duplicates/errors/etc. exist */

    console.log('URL:', window.location.href);
    console.log('Menu item:', menu_item);
    let domain_index =  window.location.href.indexOf(menu_item);
    let long_app_name = window.location.href.slice(domain_index);
    let app_name = long_app_name.slice(0, long_app_name.indexOf('/'));
    console.log('App name:', app_name);

    // First, remove active class from all menu items
    let sidebarItems = document.getElementsByClassName('sidebar-item');
    for (let i = 0; i < sidebarItems.length; i++) {
        if (sidebarItems[i].classList.contains('active'))
            sidebarItems[i].classList.remove('active');
    }

    // Then, make the one you want active
    $('nav a[href*="' + app_name+'"]').closest('a').addClass('active');
}
