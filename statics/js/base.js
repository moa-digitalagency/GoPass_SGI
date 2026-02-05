// Extracted from base.html

tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#1E3A8A',
                        secondary: '#3B82F6',
                        accent: '#10B981'
                    }
                }
            }
        }

// Global Branding Fetcher
        document.addEventListener('DOMContentLoaded', () => {
            fetch('/api/settings/public')
                .then(r => r.json())
                .then(data => {
                    // Update Sidebar (Base)
                    if (data.gopass_logo) {
                        const gp = document.getElementById('sidebar-logo-gopass');
                        const defaultTitle = document.getElementById('sidebar-default-title');

                        if (gp) {
                            gp.src = data.gopass_logo;
                            gp.classList.remove('hidden');
                        }
                        if (defaultTitle) {
                            defaultTitle.classList.add('hidden');
                        }
                    } else {
                        const defaultTitle = document.getElementById('sidebar-default-title');
                        if (defaultTitle) {
                            defaultTitle.classList.remove('hidden');
                        }
                    }

                    // Update Login Page (if present)
                    if (data.gopass_logo) {
                        const loginGp = document.getElementById('login-logo-gopass');
                        const defaultIcon = document.getElementById('login-default-icon');
                        const defaultTitle = document.getElementById('login-default-title');

                        if (loginGp) {
                            loginGp.src = data.gopass_logo;
                            loginGp.classList.remove('hidden');
                        }
                        if (defaultIcon) {
                            defaultIcon.classList.add('hidden');
                        }
                        if (defaultTitle) {
                            defaultTitle.classList.add('hidden');
                        }
                    } else {
                        const defaultIcon = document.getElementById('login-default-icon');
                        const defaultTitle = document.getElementById('login-default-title');
                        if (defaultIcon) defaultIcon.classList.remove('hidden');
                        if (defaultTitle) defaultTitle.classList.remove('hidden');
                    }

                    // Update POS/Scanner Headers (if present and extending base/using this script)
                    // Note: POS and Scanner usually don't extend base, so this script might not run there.
                    // We need to add this script logic to them separately or import it.

                    // Dispatch event for other components
                    window.dispatchEvent(new CustomEvent('settingsLoaded', { detail: data }));
                })
                .catch(console.error);
        });
// Sidebar Toggle Logic for Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('admin-sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (sidebar.classList.contains('-translate-x-full')) {
        // Open
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.remove('opacity-0'), 10);
    } else {
        // Close
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    }
}
window.toggleSidebar = toggleSidebar;
