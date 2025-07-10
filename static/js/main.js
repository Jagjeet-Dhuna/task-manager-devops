// Main JavaScript file for Task Manager App

// Global variables
let currentPage = 1;
let isLoading = false;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize the application
function initializeApp() {
    // Add loading states to forms
    setupFormSubmission();
    
    // Setup real-time updates
    setupRealTimeUpdates();
    
    // Setup tooltips
    setupTooltips();
    
    // Setup confirmation dialogs
    setupConfirmationDialogs();
    
    // Setup auto-refresh for health status
    setupHealthStatusMonitoring();
    
    console.log('Task Manager App initialized');
}

// Setup form submission with loading states
function setupFormSubmission() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                showLoading(submitBtn);
            }
        });
    });
}

// Setup real-time updates for dashboard
function setupRealTimeUpdates() {
    // Only on dashboard page
    if (window.location.pathname === '/') {
        // Update dashboard stats every 30 seconds
        setInterval(updateDashboardStats, 30000);
    }
}

// Setup Bootstrap tooltips
function setupTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Setup confirmation dialogs for destructive actions
function setupConfirmationDialogs() {
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (confirm(message)) {
                // Continue with the action
                const href = this.getAttribute('href');
                if (href) {
                    window.location.href = href;
                }
            }
        });
    });
}

// Setup health status monitoring
function setupHealthStatusMonitoring() {
    // Update health status every 60 seconds
    setInterval(updateHealthStatus, 60000);
    
    // Initial check
    updateHealthStatus();
}

// Update dashboard statistics
function updateDashboardStats() {
    if (isLoading) return;
    
    isLoading = true;
    
    fetch('/api/dashboard-stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch stats');
            }
            return response.json();
        })
        .then(data => {
            updateStatCard('total-users', data.total_users);
            updateStatCard('total-tasks', data.total_tasks);
            updateStatCard('pending-tasks', data.pending_tasks);
            updateStatCard('completed-tasks', data.completed_tasks);
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        })
        .finally(() => {
            isLoading = false;
        });
}

// Update individual stat card
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        const currentValue = parseInt(element.textContent);
        if (currentValue !== value) {
            element.textContent = value;
            element.classList.add('fade-in');
            setTimeout(() => {
                element.classList.remove('fade-in');
            }, 300);
        }
    }
}

// Update health status
function updateHealthStatus() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            const healthIndicators = document.querySelectorAll('.health-status');
            healthIndicators.forEach(indicator => {
                indicator.classList.remove('unhealthy');
                if (data.status !== 'healthy') {
                    indicator.classList.add('unhealthy');
                }
            });
        })
        .catch(error => {
            console.error('Error checking health status:', error);
            const healthIndicators = document.querySelectorAll('.health-status');
            healthIndicators.forEach(indicator => {
                indicator.classList.add('unhealthy');
            });
        });
}

// Show loading state on button
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    button.disabled = true;
    button.classList.add('loading');
    
    // Reset after 5 seconds if not reset manually
    setTimeout(() => {
        hideLoading(button, originalText);
    }, 5000);
}

// Hide loading state on button
function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
    button.classList.remove('loading');
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    const firstChild = container.firstChild;
    container.insertBefore(alertDiv, firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Format relative time
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return formatDate(dateString);
}

// Validate email format
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate form fields
function validateForm(form) {
    const errors = [];
    
    // Check required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            errors.push(`${field.labels[0]?.textContent || field.name} is required`);
        }
    });
    
    // Check email fields
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !validateEmail(field.value)) {
            errors.push('Please enter a valid email address');
        }
    });
    
    return errors;
}

// Handle API errors
function handleApiError(error, defaultMessage = 'An error occurred') {
    console.error('API Error:', error);
    
    let message = defaultMessage;
    if (error.response) {
        error.response.json().then(data => {
            message = data.error || data.message || defaultMessage;
            showNotification(message, 'danger');
        });
    } else {
        showNotification(message, 'danger');
    }
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Setup live search
function setupLiveSearch(searchInput, searchFunction) {
    const debouncedSearch = debounce(searchFunction, 300);
    searchInput.addEventListener('input', debouncedSearch);
}

// Local storage helpers
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return defaultValue;
    }
}

// Theme management
function initializeTheme() {
    const savedTheme = loadFromLocalStorage('theme', 'light');
    setTheme(savedTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    saveToLocalStorage('theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Export functions for use in other scripts
window.TaskManager = {
    showNotification,
    formatDate,
    formatRelativeTime,
    validateEmail,
    validateForm,
    handleApiError,
    showLoading,
    hideLoading,
    saveToLocalStorage,
    loadFromLocalStorage,
    debounce,
    setupLiveSearch
};

// Initialize theme on load
initializeTheme();