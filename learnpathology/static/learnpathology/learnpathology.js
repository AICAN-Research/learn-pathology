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
    let app_name = '';

    let url_is_task_do = location.href.includes('multiple_choice/do')
        || location.href.includes('free_text/do')
        || location.href.includes('click_question/do')
        || location.href.includes('one_to_one/do')
        || location.href.includes('many_to_one/do');
    let url_is_task_edit = location.href.includes('multiple_choice/edit')
        || location.href.includes('free_text/edit')
        || location.href.includes('click_question/edit')
        || location.href.includes('one_to_one/edit')
        || location.href.includes('many_to_one/edit');

    if (location.href.includes('slide')){
        menu_item = 'slide';
    } else if (location.href.includes('course')) {
        menu_item = 'course';
    // } else if (location.href.includes('task/list')) {
    } else if (location.href.includes('task')) {
        menu_item = 'task';
    } else if (url_is_task_do || url_is_task_edit) {
        menu_item = '';
        app_name = 'task';
    } else if (location.href.includes('tag/')) {
        menu_item = 'tag';
    } else {
        return;
    }
    /* TODO: Check menu options that no duplicates/errors/etc. exist */

    if (!(menu_item === '') && (app_name === '')) {
        let domain_index =  window.location.href.indexOf(menu_item);
        let long_app_name = window.location.href.slice(domain_index);
        app_name = long_app_name.slice(0, long_app_name.indexOf('/'));
    } else {
        app_name = 'task';
    }
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
