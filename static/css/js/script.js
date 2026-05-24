// General JavaScript for the Face Attendance System

document.addEventListener('DOMContentLoaded', function() {
    console.log('FACEATTEND System Initialized');
    
    // Initialize all systems
    initSidebar();
    initTooltips();
    initAnimations();
    initFormValidation();
});

// ==================== SIDEBAR FUNCTIONALITY ====================
function initSidebar() {
    console.log('Initializing sidebar...');
    
    // Get sidebar elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.getElementById('mainContent');
    const searchInput = document.getElementById('searchInput');

    // Check if required elements exist
    if (!sidebar || !sidebarToggle) {
        console.error('Sidebar or toggle button not found!');
        return;
    }

    console.log('Sidebar elements found:', {
        sidebar: !!sidebar,
        toggle: !!sidebarToggle,
        close: !!sidebarClose,
        overlay: !!sidebarOverlay,
        mainContent: !!mainContent
    });

    // Toggle sidebar function
    function toggleSidebar() {
        console.log('Toggling sidebar');
        const isOpening = !sidebar.classList.contains('active');
        
        sidebar.classList.toggle('active');
        
        if (sidebarOverlay) {
            sidebarOverlay.classList.toggle('active');
        }
        
        if (mainContent) {
            mainContent.classList.toggle('sidebar-open');
        }

        // Prevent body scroll when sidebar is open on mobile
        if (window.innerWidth < 1024) {
            document.body.style.overflow = isOpening ? 'hidden' : '';
        }
    }

    // Close sidebar function
    function closeSidebar() {
        console.log('Closing sidebar');
        sidebar.classList.remove('active');
        
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('active');
        }
        
        if (mainContent) {
            mainContent.classList.remove('sidebar-open');
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    // Add event listeners
    sidebarToggle.addEventListener('click', toggleSidebar);
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar when pressing Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024 && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Search functionality
    if (searchInput) {
        const debouncedSearch = debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            filterSidebarItems(searchTerm);
        }, 300);

        searchInput.addEventListener('input', debouncedSearch);
        
        // Clear search on escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                filterSidebarItems('');
                this.blur();
            }
        });
    }

    // Set active page in sidebar
    setActiveSidebarPage();

    console.log('Sidebar initialized successfully!');
}

// Filter sidebar items based on search
function filterSidebarItems(searchTerm) {
    const navItems = document.querySelectorAll('.nav-item');
    const navSections = document.querySelectorAll('.nav-section');
    
    let visibleItems = 0;
    
    navItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (searchTerm === '' || text.includes(searchTerm)) {
            item.style.display = 'flex';
            visibleItems++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Hide empty sections
    navSections.forEach(section => {
        const itemsInSection = section.querySelectorAll('.nav-item');
        const visibleInSection = section.querySelectorAll('.nav-item[style="display: flex;"]');
        
        if (visibleInSection.length === 0 && searchTerm !== '') {
            section.style.display = 'none';
        } else {
            section.style.display = 'block';
        }
    });
}

// Add active class to current page in sidebar
function setActiveSidebarPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        // Remove active class from all links first
        link.classList.remove('active');
        
        // Add active class to current page
        if (href && currentPath === href) {
            link.classList.add('active');
        }
    });
}

// ==================== TOOLTIP SYSTEM ====================
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip], [title]');
    
    tooltipElements.forEach(el => {
        const tooltipText = el.getAttribute('data-tooltip') || el.getAttribute('title');
        
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            // Position tooltip
            const rect = this.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            tooltip.style.left = (rect.left + (rect.width / 2) - (tooltipRect.width / 2)) + 'px';
            tooltip.style.top = (rect.top - tooltipRect.height - 8) + 'px';
            
            // Remove title to prevent default tooltip
            if (el.getAttribute('title')) {
                el.setAttribute('data-original-title', el.getAttribute('title'));
                el.removeAttribute('title');
            }
            
            this.addEventListener('mouseleave', function() {
                if (document.body.contains(tooltip)) {
                    document.body.removeChild(tooltip);
                }
                // Restore title if it existed
                const originalTitle = el.getAttribute('data-original-title');
                if (originalTitle) {
                    el.setAttribute('title', originalTitle);
                }
            }, { once: true });
        });
    });
}

// ==================== ANIMATION SYSTEM ====================
function initAnimations() {
    // Add animation class to elements when they come into view
    const animatedElements = document.querySelectorAll('.slide-in-up, .fade-in, .hover-lift');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, { 
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => {
        observer.observe(el);
    });

    // Add hover effects to interactive elements
    initHoverEffects();
}

function initHoverEffects() {
    // Card hover effects
    const cards = document.querySelectorAll('.feature-card, .stat-card, .lecture-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Button click effects
    const buttons = document.querySelectorAll('.btn, .btn-quick, .btn-primary, .btn-secondary');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                transform: scale(0);
                animation: ripple-animation 0.6s linear;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                if (ripple.parentNode === this) {
                    this.removeChild(ripple);
                }
            }, 600);
        });
    });
}

// ==================== FORM VALIDATION SYSTEM ====================
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearError(this);
            });
        });
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Please fix the errors in the form.', 'error');
                
                // Scroll to first error
                const firstError = this.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(input) {
    const value = input.value.trim();
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required';
    }
    // Email validation
    else if (input.type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        message = 'Please enter a valid email address';
    }
    // Student ID validation
    else if (input.id === 'student_id' && value && !/^[a-zA-Z0-9\-_]+$/.test(value)) {
        isValid = false;
        message = 'Student ID can only contain letters, numbers, hyphens, and underscores';
    }
    // Password strength validation
    else if (input.type === 'password' && value && value.length < 6) {
        isValid = false;
        message = 'Password must be at least 6 characters long';
    }
    // URL validation
    else if (input.type === 'url' && value && !isValidUrl(value)) {
        isValid = false;
        message = 'Please enter a valid URL';
    }
    
    if (!isValid) {
        highlightError(input, message);
    } else {
        clearError(input);
        highlightSuccess(input);
    }
    
    return isValid;
}

function highlightError(input, message) {
    clearError(input);
    
    const error = document.createElement('div');
    error.className = 'error-message';
    error.textContent = message;
    error.style.cssText = `
        color: #dc2626;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    
    input.classList.add('error');
    input.parentNode.appendChild(error);
}

function highlightSuccess(input) {
    input.classList.remove('error');
    input.classList.add('success');
    
    // Remove success class after 2 seconds
    setTimeout(() => {
        input.classList.remove('success');
    }, 2000);
}

function clearError(input) {
    input.classList.remove('error');
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// ==================== UTILITY FUNCTIONS ====================
// AJAX helper functions
function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options)
        .then(async response => {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Network response was not ok');
            }
            
            return data;
        })
        .catch(error => {
            console.error('API request failed:', error);
            showNotification(error.message || 'Request failed. Please try again.', 'error');
            throw error;
        });
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    });
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove after delay
    if (duration > 0) {
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
    }
    
    return notification;
}

function getNotificationIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || icons.info;
}

// Export to CSV function
function exportToCSV(data, filename = 'export.csv') {
    if (!data || !Array.isArray(data) || data.length === 0) {
        showNotification('No data to export', 'error');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const cell = row[header] || '';
            // Escape quotes and wrap in quotes if contains comma
            return `"${String(cell).replace(/"/g, '""')}"`;
        }).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification(`Data exported successfully as ${filename}`, 'success');
}

// Date formatting helper
function formatDate(date, format = 'yyyy-mm-dd') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('yyyy', year)
        .replace('mm', month)
        .replace('dd', day)
        .replace('HH', hours)
        .replace('MM', minutes)
        .replace('SS', seconds);
}

// Debounce function for search inputs
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Local storage helpers
function setStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function getStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
    }
}

function removeStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Error removing from localStorage:', error);
        return false;
    }
}

// ==================== GLOBAL EXPORTS ====================
// Make functions available globally
window.FACEATTEND = {
    showNotification,
    apiRequest,
    exportToCSV,
    formatDate,
    debounce,
    throttle,
    setStorage,
    getStorage,
    removeStorage
};

console.log('FACEATTEND JavaScript loaded successfully!');

// FACEATTEND Sidebar System
console.log('🎯 FACEATTEND System Loading...');

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ script.js loaded successfully");

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarClose = document.getElementById("sidebarClose");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const mainContent = document.getElementById("mainContent");

    // === Sidebar Toggle ===
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            const isClosed = sidebar.classList.contains("closed");
            sidebar.classList.toggle("closed", !isClosed);
            sidebarOverlay.classList.toggle("active", isClosed);
            mainContent.classList.toggle("full-width", !isClosed);
        });
    }

    // === Sidebar Close Button ===
    if (sidebarClose) {
        sidebarClose.addEventListener("click", () => {
            sidebar.classList.add("closed");
            sidebarOverlay.classList.remove("active");
            mainContent.classList.add("full-width");
        });
    }

    // === Overlay Click ===
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", () => {
            sidebar.classList.add("closed");
            sidebarOverlay.classList.remove("active");
            mainContent.classList.add("full-width");
        });
    }

    // === Auto-hide Alerts ===
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            alert.classList.add("fade-out");
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });
});
// Function to mark lecture as complete and record absences
function markLectureComplete(lectureId, lectureName) {
    if (!confirm(`Mark "${lectureName}" as complete? This will record absent students for today.`)) {
        return;
    }
    
    fetch('/mark_lecture_complete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            lecture_id: lectureId,
            date: new Date().toISOString().split('T')[0]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ ${data.message}`);
            // Refresh the page to update absence display
            location.reload();
        } else {
            alert(`❌ Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ Failed to mark lecture complete');
    });
}

// Function to view absent students for a lecture
function viewAbsentStudents(lectureId, lectureName) {
    fetch(`/get_absent_students/${lectureId}?date=${new Date().toISOString().split('T')[0]}`)
    .then(response => response.json())
    .then(data => {
        if (data.absent_students && data.absent_students.length > 0) {
            let message = `Absent students for ${lectureName}:\n\n`;
            data.absent_students.forEach(student => {
                message += `• ${student.name} (${student.student_id})\n`;
            });
            alert(message);
        } else {
            alert(`✅ No absent students for ${lectureName} today.`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ Failed to fetch absent students');
    });
}

// Utility functions
function showNotification(message, type = 'info') {
    alert(message); // Simple alert for now
}
