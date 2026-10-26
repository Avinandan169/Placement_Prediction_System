/**
 * Shared Unified Navigation & Layout Shell for Placement Prediction System
 * Automatically renders sidebar, mobile navigation, topbar with active indicators,
 * user authentication state, and live system status pills.
 */

(function () {
    const NAV_ITEMS = [
        {
            group: "OVERVIEW",
            items: [
                { id: "dashboard", label: "Dashboard", href: "dashboard.html", icon: "fa-chart-pie" }
            ]
        },
        {
            group: "PREDICTIVE ANALYTICS (CSE3141)",
            items: [
                { id: "dataset", label: "Dataset Management", href: "dataset.html", icon: "fa-database" },
                { id: "eda", label: "Exploratory Analysis", href: "eda.html", icon: "fa-chart-column" },
                { id: "models", label: "Model Training & Eval", href: "models.html", icon: "fa-cubes" },
                { id: "predict", label: "Placement Prediction", href: "predict.html", icon: "fa-wand-magic-sparkles" },
                { id: "explainability", label: "Model Explainability", href: "explainability.html", icon: "fa-magnifying-glass-chart" }
            ]
        },
        {
            group: "AI & SOFT COMPUTING (CSE3121)",
            items: [
                { id: "readiness", label: "Fuzzy Readiness", href: "readiness.html", icon: "fa-brain" },
                { id: "planner", label: "A* Skill Planner", href: "planner.html", icon: "fa-route" }
            ]
        },
        {
            group: "CAREER TOOLS",
            items: [
                { id: "profile", label: "Resume Analysis", href: "profile.html", icon: "fa-file-lines" },
                { id: "results", label: "Job Matching", href: "results.html", icon: "fa-briefcase" },
                { id: "softskills", label: "Communication Test", href: "soft-skills.html", icon: "fa-microphone" },
                { id: "test", label: "Technical Quiz", href: "test.html", icon: "fa-vial-circle-check" },
                { id: "chat", label: "AI Career Assistant", href: "conversation.html", icon: "fa-comments" }
            ]
        },
        {
            group: "SYSTEM",
            items: [
                { id: "history", label: "Prediction History", href: "history.html", icon: "fa-clock-rotate-left" },
                { id: "officer", label: "Officer Console", href: "officer-dashboard.html", icon: "fa-id-badge" }
            ]
        }
    ];

    function getCurrentPageId() {
        const path = window.location.pathname;
        const filename = path.substring(path.lastIndexOf('/') + 1) || 'index.html';

        if (filename.includes('dashboard')) return 'dashboard';
        if (filename.includes('dataset')) return 'dataset';
        if (filename.includes('eda')) return 'eda';
        if (filename.includes('models')) return 'models';
        if (filename.includes('predict')) return 'predict';
        if (filename.includes('explain')) return 'explainability';
        if (filename.includes('readiness')) return 'readiness';
        if (filename.includes('planner')) return 'planner';
        if (filename.includes('profile')) return 'profile';
        if (filename.includes('results')) return 'results';
        if (filename.includes('soft-skills') || filename.includes('communication')) return 'softskills';
        if (filename.includes('test')) return 'test';
        if (filename.includes('conversation')) return 'chat';
        if (filename.includes('history')) return 'history';
        if (filename.includes('officer')) return 'officer';
        return 'dashboard';
    }

    function initShell() {
        const currentPageId = getCurrentPageId();
        const userEmail = localStorage.getItem('currentUserEmail') || localStorage.getItem('userEmail') || localStorage.getItem('email') || 'Guest';
        const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
        const role = localStorage.getItem('userRole') || 'student';

        // 1. Sidebar HTML
        let navHtml = `
            <div class="sidebar-brand">
                <a href="index.html" class="brand-link">
                    <div class="brand-icon"><i class="fa-solid fa-graduation-cap"></i></div>
                    <div class="brand-text">
                        <span class="brand-title">PredictPlacement</span>
                        <span class="brand-subtitle">AI & Analytics Platform</span>
                    </div>
                </a>
            </div>
            <nav class="sidebar-nav" aria-label="Main Navigation">
        `;

        NAV_ITEMS.forEach(group => {
            navHtml += `<div class="nav-group-title">${group.group}</div>`;
            navHtml += `<ul class="nav-list">`;
            group.items.forEach(item => {
                // If officer console, only highlight or show appropriate role
                const isActive = item.id === currentPageId ? 'active' : '';
                navHtml += `
                    <li class="nav-item">
                        <a href="${item.href}" class="nav-link ${isActive}" data-id="${item.id}">
                            <i class="fa-solid ${item.icon} nav-icon"></i>
                            <span class="nav-label">${item.label}</span>
                        </a>
                    </li>
                `;
            });
            navHtml += `</ul>`;
        });

        navHtml += `
            </nav>
            <div class="sidebar-footer">
                <div class="dataset-status-pill" id="global-dataset-status" title="Active placement training dataset">
                    <span class="status-dot"></span>
                    <span class="dataset-text">Krooz Recruitment CSV</span>
                </div>
            </div>
        `;

        // Render into element #sidebar-container or .app-sidebar
        const sidebarTarget = document.getElementById('sidebar-container') || document.querySelector('.app-sidebar');
        if (sidebarTarget) {
            sidebarTarget.innerHTML = navHtml;
        }

        // 2. Render Topbar into element #topbar-container or .app-topbar
        const topbarTarget = document.getElementById('topbar-container') || document.querySelector('.app-topbar');
        if (topbarTarget && !topbarTarget.dataset.initialized) {
            topbarTarget.dataset.initialized = 'true';
            const pageTitle = document.title.split('-')[0].trim() || 'Dashboard';
            
            topbarTarget.innerHTML = `
                <div class="topbar-left">
                    <button class="mobile-menu-btn" id="mobile-toggle" aria-label="Toggle navigation drawer">
                        <i class="fa-solid fa-bars"></i>
                    </button>
                    <div class="breadcrumbs">
                        <span class="crumb-root"><i class="fa-solid fa-house"></i></span>
                        <span class="crumb-separator">/</span>
                        <span class="crumb-current">${pageTitle}</span>
                    </div>
                </div>
                <div class="topbar-right">
                    <div class="system-status-badge">
                        <span class="status-indicator-dot"></span>
                        <span class="status-label">Pipeline Active</span>
                    </div>
                    <div class="user-profile-menu">
                        <div class="user-avatar-circle">
                            <i class="fa-solid fa-user"></i>
                        </div>
                        <div class="user-details-box">
                            <span class="user-display-email" id="header-user-email">${userEmail}</span>
                            <span class="user-role-badge">${role.toUpperCase()}</span>
                        </div>
                        ${token ? `
                            <button id="header-logout-btn" class="btn btn-outline btn-sm logout-btn" title="Sign out">
                                <i class="fa-solid fa-arrow-right-from-bracket"></i>
                            </button>
                        ` : `
                            <a href="login.html" class="btn btn-primary btn-sm login-link-btn">
                                Sign In
                            </a>
                        `}
                    </div>
                </div>
            `;

            const logoutBtn = document.getElementById('header-logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    localStorage.removeItem('token');
                    localStorage.removeItem('userEmail');
                    localStorage.removeItem('email');
                    localStorage.removeItem('userRole');
                    window.location.href = 'login.html';
                });
            }
        }

        // 3. Mobile Navigation Drawer Toggle
        const toggleBtn = document.getElementById('mobile-toggle');
        const sidebar = sidebarTarget || document.querySelector('.app-sidebar');
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
            // Close when clicking outside
            document.addEventListener('click', (e) => {
                if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initShell);
    } else {
        initShell();
    }
})();
