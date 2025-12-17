// UniPortal Main JavaScript File
console.log('UniPortal PWA loaded successfully');

// PWA utility functions
window.UniPortal = {
  // Check if app is running as PWA
  isPWA: function() {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
  },
  
  // Show install prompt
  showInstallPrompt: function() {
    if (window.deferredPrompt) {
      window.deferredPrompt.prompt();
      window.deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt');
        }
        window.deferredPrompt = null;
      });
    }
  }
};

// PWA install prompt handling
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  window.deferredPrompt = e;
});

window.addEventListener('appinstalled', (evt) => {
  console.log('UniPortal PWA was installed');
});

// Smooth page transitions
window.UniPortal.smoothTransition = function(url) {
  // Show loading overlay
  const loadingOverlay = document.createElement('div');
  loadingOverlay.className = 'loading-screen';
  loadingOverlay.innerHTML = `
    <div class="loading-spinner"></div>
    <div class="loading-text">UniPortal</div>
    <div class="loading-subtext">Loading...</div>
  `;
  document.body.appendChild(loadingOverlay);
  
  // Navigate after short delay
  setTimeout(() => {
    window.location.href = url;
  }, 200);
};

// Add smooth transitions to navigation links
document.addEventListener('DOMContentLoaded', function() {
  // Add transition effect to all navigation links
  const navLinks = document.querySelectorAll('.nav-item, .sidebar-nav a');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href && href !== '#' && !href.startsWith('javascript:') && !this.hasAttribute('onclick')) {
        e.preventDefault();
        window.UniPortal.smoothTransition(href);
      }
    });
  });
  
  // Add transition effect to form submissions
  const forms = document.querySelectorAll('form[method="POST"]');
  forms.forEach(form => {
    form.addEventListener('submit', function() {
      const loadingOverlay = document.createElement('div');
      loadingOverlay.className = 'loading-screen';
      loadingOverlay.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-text">Processing...</div>
        <div class="loading-subtext">Please wait...</div>
      `;
      document.body.appendChild(loadingOverlay);
    });
  });
});