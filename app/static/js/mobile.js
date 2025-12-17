/**
 * UniPortal Mobile Enhancement JavaScript
 * Provides device-specific functionality and improved mobile UX
 */

class MobileEnhancer {
    constructor() {
        this.deviceInfo = this.detectDevice();
        this.init();
    }

    detectDevice() {
        const userAgent = navigator.userAgent;
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        const isTablet = /iPad|Android.*Tablet|Kindle|Silk|PlayBook/i.test(userAgent);
        const isIOS = /iPad|iPhone|iPod/.test(userAgent);
        const isAndroid = /Android/.test(userAgent);
        
        return {
            isMobile: isMobile && !isTablet,
            isTablet: isTablet,
            isDesktop: !isMobile && !isTablet,
            isIOS: isIOS,
            isAndroid: isAndroid,
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            pixelRatio: window.devicePixelRatio || 1
        };
    }

    init() {
        this.setupViewportMeta();
        this.setupMobileNavigation();
        this.setupTouchEnhancements();
        this.setupKeyboardHandling();
        this.setupOrientationHandling();
        this.setupScrollEnhancements();
        
        // Add device classes to body
        this.addDeviceClasses();
        
        // Initialize mobile-specific features
        if (this.deviceInfo.isMobile) {
            this.initMobileFeatures();
        }
    }

    setupViewportMeta() {
        // Ensure proper viewport meta tag
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        // Set optimal viewport for mobile
        if (this.deviceInfo.isMobile) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
        } else {
            viewport.content = 'width=device-width, initial-scale=1.0';
        }
    }

    addDeviceClasses() {
        const body = document.body;
        
        // Add device type classes
        if (this.deviceInfo.isMobile) body.classList.add('mobile-device');
        if (this.deviceInfo.isTablet) body.classList.add('tablet-device');
        if (this.deviceInfo.isDesktop) body.classList.add('desktop-device');
        if (this.deviceInfo.isIOS) body.classList.add('ios-device');
        if (this.deviceInfo.isAndroid) body.classList.add('android-device');
        
        // Add screen size classes
        if (this.deviceInfo.screenWidth <= 480) body.classList.add('small-screen');
        else if (this.deviceInfo.screenWidth <= 768) body.classList.add('medium-screen');
        else body.classList.add('large-screen');
    }

    setupMobileNavigation() {
        // Enhanced mobile sidebar toggle
        const toggleButton = document.getElementById('mobileMenuToggle');
        const sidebar = document.getElementById('sidebar');
        
        if (toggleButton && sidebar) {
            toggleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMobileSidebar();
            });
            
            // Close sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (this.deviceInfo.isMobile && sidebar.classList.contains('active')) {
                    if (!sidebar.contains(e.target) && !toggleButton.contains(e.target)) {
                        this.closeMobileSidebar();
                    }
                }
            });
            
            // Close sidebar on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && sidebar.classList.contains('active')) {
                    this.closeMobileSidebar();
                }
            });
        }
    }

    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const body = document.body;
        
        if (sidebar) {
            sidebar.classList.toggle('active');
            body.classList.toggle('menu-open');
            
            // Only prevent body scroll when menu is open, but allow main content scroll
            if (sidebar.classList.contains('active')) {
                // Don't set overflow hidden on body, let CSS handle it
                body.style.position = 'fixed';
                body.style.width = '100%';
            } else {
                body.style.position = '';
                body.style.width = '';
            }
        }
    }

    closeMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const body = document.body;
        
        if (sidebar && sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
            body.classList.remove('menu-open');
            body.style.position = '';
            body.style.width = '';
        }
    }

    setupTouchEnhancements() {
        // Add touch feedback to interactive elements
        const interactiveElements = document.querySelectorAll('.btn, .nav-item, .card, .glass-card');
        
        interactiveElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.classList.add('touch-active');
            });
            
            element.addEventListener('touchend', () => {
                setTimeout(() => {
                    element.classList.remove('touch-active');
                }, 150);
            });
        });
    }

    setupKeyboardHandling() {
        if (!this.deviceInfo.isMobile) return;
        
        // Handle virtual keyboard on mobile
        let initialViewportHeight = window.innerHeight;
        
        window.addEventListener('resize', () => {
            const currentHeight = window.innerHeight;
            const heightDifference = initialViewportHeight - currentHeight;
            
            // If height decreased significantly, keyboard is likely open
            if (heightDifference > 150) {
                document.body.classList.add('keyboard-open');
                
                // Scroll active input into view
                const activeElement = document.activeElement;
                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                    setTimeout(() => {
                        activeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 300);
                }
            } else {
                document.body.classList.remove('keyboard-open');
            }
        });
        
        // Prevent zoom on input focus (iOS)
        if (this.deviceInfo.isIOS) {
            const inputs = document.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            });
        }
    }

    setupOrientationHandling() {
        window.addEventListener('orientationchange', () => {
            // Close mobile sidebar on orientation change
            this.closeMobileSidebar();
            
            // Recalculate device info
            setTimeout(() => {
                this.deviceInfo = this.detectDevice();
                this.addDeviceClasses();
            }, 500);
        });
    }

    setupScrollEnhancements() {
        // Smooth scrolling for mobile
        if (this.deviceInfo.isMobile) {
            document.documentElement.style.scrollBehavior = 'smooth';
            
            // Add momentum scrolling for iOS
            if (this.deviceInfo.isIOS) {
                document.body.style.webkitOverflowScrolling = 'touch';
            }
        }
        
        // Hide mobile top bar on scroll down, show on scroll up
        let lastScrollTop = 0;
        const mobileTopBar = document.querySelector('.mobile-top-bar');
        
        if (mobileTopBar && this.deviceInfo.isMobile) {
            window.addEventListener('scroll', () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                if (scrollTop > lastScrollTop && scrollTop > 100) {
                    // Scrolling down
                    mobileTopBar.style.transform = 'translateY(-100%)';
                } else {
                    // Scrolling up
                    mobileTopBar.style.transform = 'translateY(0)';
                }
                
                lastScrollTop = scrollTop;
            });
        }
    }

    initMobileFeatures() {
        // Fix scrolling issues
        this.fixScrolling();
        
        // Add pull-to-refresh (if supported)
        this.setupPullToRefresh();
        
        // Add haptic feedback (if supported)
        this.setupHapticFeedback();
        
        // Optimize images for mobile
        this.optimizeImagesForMobile();
    }

    fixScrolling() {
        // AGGRESSIVE scrolling fix
        const html = document.documentElement;
        const body = document.body;
        
        // Force enable scrolling on html and body
        html.style.overflow = 'auto';
        html.style.overflowY = 'auto';
        html.style.overflowX = 'hidden';
        html.style.height = 'auto';
        html.style.webkitOverflowScrolling = 'touch';
        
        body.style.overflow = 'auto';
        body.style.overflowY = 'auto';
        body.style.overflowX = 'hidden';
        body.style.height = 'auto';
        body.style.minHeight = '100vh';
        body.style.webkitOverflowScrolling = 'touch';
        body.style.position = 'static';
        
        // Force main content to be scrollable
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.overflow = 'visible';
            mainContent.style.overflowY = 'visible';
            mainContent.style.overflowX = 'hidden';
            mainContent.style.height = 'auto';
            mainContent.style.minHeight = '100vh';
            mainContent.style.webkitOverflowScrolling = 'touch';
            mainContent.style.position = 'static';
        }
        
        // Remove any height constraints from dashboard body
        if (body.classList.contains('dashboard-page')) {
            body.style.height = 'auto';
            body.style.maxHeight = 'none';
        }
        
        // Fix iOS Safari scrolling issues
        if (this.deviceInfo.isIOS) {
            // Prevent zoom on double tap
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function (event) {
                const now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
            
            // Fix viewport height issues
            const setViewportHeight = () => {
                document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
            };
            
            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
            window.addEventListener('orientationchange', () => {
                setTimeout(setViewportHeight, 500);
            });
        }
        
        // Add a test div to force scrolling
        if (this.deviceInfo.isMobile) {
            const testDiv = document.createElement('div');
            testDiv.style.height = '1px';
            testDiv.style.width = '100%';
            testDiv.style.position = 'absolute';
            testDiv.style.bottom = '-50px';
            testDiv.style.left = '0';
            testDiv.style.pointerEvents = 'none';
            document.body.appendChild(testDiv);
        }
    }

    setupPullToRefresh() {
        // Simple pull-to-refresh implementation
        let startY = 0;
        let currentY = 0;
        let pullDistance = 0;
        const threshold = 100;
        
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        });
        
        document.addEventListener('touchmove', (e) => {
            if (window.scrollY === 0 && startY) {
                currentY = e.touches[0].clientY;
                pullDistance = currentY - startY;
                
                if (pullDistance > 0 && pullDistance < threshold) {
                    // Visual feedback for pull
                    document.body.style.transform = `translateY(${pullDistance * 0.5}px)`;
                }
            }
        });
        
        document.addEventListener('touchend', () => {
            if (pullDistance > threshold) {
                // Trigger refresh
                window.location.reload();
            }
            
            // Reset
            document.body.style.transform = '';
            startY = 0;
            pullDistance = 0;
        });
    }

    setupHapticFeedback() {
        // Add haptic feedback for supported devices
        if ('vibrate' in navigator) {
            const buttons = document.querySelectorAll('.btn, .nav-item');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    navigator.vibrate(10); // Short vibration
                });
            });
        }
    }

    optimizeImagesForMobile() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // Add loading="lazy" for better performance
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Add error handling
            img.addEventListener('error', () => {
                img.style.display = 'none';
            });
        });
    }

    // Utility methods
    static isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    static getScreenSize() {
        return {
            width: window.innerWidth,
            height: window.innerHeight
        };
    }

    static addMobileClass(element, className) {
        if (MobileEnhancer.isMobileDevice()) {
            element.classList.add(className);
        }
    }
}

// IMMEDIATE scrolling fix - runs before DOM is ready
(function() {
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        // Force enable scrolling immediately
        const style = document.createElement('style');
        style.textContent = `
            html, body {
                overflow: auto !important;
                overflow-y: auto !important;
                height: auto !important;
                position: static !important;
                -webkit-overflow-scrolling: touch !important;
            }
            body.dashboard-page {
                overflow: auto !important;
                height: auto !important;
                position: static !important;
            }
            .main-content {
                overflow: visible !important;
                height: auto !important;
                position: static !important;
            }
        `;
        document.head.appendChild(style);
        
        // Force scrolling on load
        window.addEventListener('load', function() {
            document.documentElement.style.overflow = 'auto';
            document.body.style.overflow = 'auto';
            document.body.style.height = 'auto';
            document.body.style.position = 'static';
        });
    }
})();

// Initialize mobile enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileEnhancer = new MobileEnhancer();
});

// Global functions for backward compatibility
function toggleMobileSidebar() {
    if (window.mobileEnhancer) {
        window.mobileEnhancer.toggleMobileSidebar();
    }
}

// Debug function to check scrolling
function debugScrolling() {
    const html = document.documentElement;
    const body = document.body;
    const mainContent = document.querySelector('.main-content');
    
    console.log('=== SCROLLING DEBUG ===');
    console.log('HTML overflow:', getComputedStyle(html).overflow);
    console.log('HTML overflowY:', getComputedStyle(html).overflowY);
    console.log('HTML height:', getComputedStyle(html).height);
    console.log('BODY overflow:', getComputedStyle(body).overflow);
    console.log('BODY overflowY:', getComputedStyle(body).overflowY);
    console.log('BODY height:', getComputedStyle(body).height);
    console.log('BODY position:', getComputedStyle(body).position);
    
    if (mainContent) {
        console.log('MAIN overflow:', getComputedStyle(mainContent).overflow);
        console.log('MAIN overflowY:', getComputedStyle(mainContent).overflowY);
        console.log('MAIN height:', getComputedStyle(mainContent).height);
        console.log('MAIN position:', getComputedStyle(mainContent).position);
    }
    
    console.log('Document height:', document.documentElement.scrollHeight);
    console.log('Window height:', window.innerHeight);
    console.log('Can scroll:', document.documentElement.scrollHeight > window.innerHeight);
}

// Make debug function available globally
window.debugScrolling = debugScrolling;

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileEnhancer;
}

// Professional Sidebar Enhancements
class SidebarEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupSidebarScrolling();
        this.setupSidebarVisibility();
    }

    setupSidebarScrolling() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        // Check if sidebar content is scrollable
        const checkScrollable = () => {
            const isScrollable = sidebar.scrollHeight > sidebar.clientHeight;
            sidebar.classList.toggle('scrollable', isScrollable);
        };

        // Check on load and resize
        checkScrollable();
        window.addEventListener('resize', checkScrollable);

        // Add smooth scrolling behavior
        sidebar.addEventListener('wheel', (e) => {
            // Allow natural scrolling but ensure it's smooth
            sidebar.style.scrollBehavior = 'smooth';
        });

        // Reset scroll behavior after scrolling
        let scrollTimeout;
        sidebar.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                sidebar.style.scrollBehavior = 'auto';
            }, 150);
        });
    }

    setupSidebarVisibility() {
        const sidebar = document.querySelector('.sidebar');
        const sidebarNav = document.querySelector('.sidebar-nav');
        
        if (!sidebar || !sidebarNav) return;

        // Ensure sidebar is properly visible and scrollable
        const ensureVisibility = () => {
            // Force proper display and positioning
            if (window.innerWidth >= 769) {
                sidebar.style.display = 'flex';
                sidebar.style.position = 'sticky';
                sidebar.style.top = '0';
                sidebar.style.height = '100vh';
                sidebar.style.overflowY = 'auto';
                sidebar.style.overflowX = 'hidden';
                
                // Ensure navigation is scrollable
                sidebarNav.style.overflowY = 'auto';
                sidebarNav.style.overflowX = 'hidden';
                sidebarNav.style.flex = '1';
                sidebarNav.style.minHeight = '0';
            }
        };

        // Apply on load and resize
        ensureVisibility();
        window.addEventListener('resize', ensureVisibility);
        window.addEventListener('orientationchange', () => {
            setTimeout(ensureVisibility, 500);
        });
    }
}

// Initialize sidebar enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth >= 769) {
        new SidebarEnhancer();
    }
});

// Also initialize on window resize to desktop
window.addEventListener('resize', () => {
    if (window.innerWidth >= 769 && !window.sidebarEnhancer) {
        window.sidebarEnhancer = new SidebarEnhancer();
    }
});