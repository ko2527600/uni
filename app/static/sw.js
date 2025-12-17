const CACHE_NAME = 'uniportal-v3-offline';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/css/style.css',
  '/static/css/fontawesome-local.css',
  '/static/css/icons.css',
  '/static/css/mobile.css',
  '/static/css/mobile-scroll-fix.css',
  '/static/script.js',
  '/static/js/mobile.js',
  '/static/logo.png',
  '/static/icon-192x192.png',
  '/static/icon-512x512.png',
  '/static/manifest.json',
  '/static/background.jpg'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
        console.log('Cache installation failed:', error);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if available
        if (response) {
          return response;
        }
        
        // Otherwise fetch from network with error handling
        return fetch(event.request).catch(error => {
          console.log('Fetch failed for:', event.request.url, error);
          
          // For navigation requests, return a fallback page
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
          
          // For other requests, return a network error response
          return new Response('Network error', {
            status: 408,
            headers: { 'Content-Type': 'text/plain' }
          });
        });
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Push event - show notifications
self.addEventListener('push', event => {
  console.log('Push event received:', event);
  
  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (e) {
      notificationData = {
        title: 'UniPortal Notification',
        body: event.data.text() || 'You have a new notification',
        icon: '/static/icon-192x192.png',
        badge: '/static/icon-192x192.png'
      };
    }
  } else {
    notificationData = {
      title: 'UniPortal Notification',
      body: 'You have a new notification',
      icon: '/static/icon-192x192.png',
      badge: '/static/icon-192x192.png'
    };
  }

  const options = {
    body: notificationData.body,
    icon: notificationData.icon || '/static/icon-192x192.png',
    badge: notificationData.badge || '/static/icon-192x192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: notificationData.primaryKey || 1,
      url: notificationData.url || '/'
    },
    actions: [
      {
        action: 'explore',
        title: 'Open UniPortal',
        icon: '/static/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icon-192x192.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  );
});

// Notification click event - handle user interaction
self.addEventListener('notificationclick', event => {
  console.log('Notification click received:', event);
  
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  // Get the URL to open (default to home page)
  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(clientList => {
      // Check if there's already a window/tab open with the target URL
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      
      // If no existing window/tab, open a new one
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Background sync (for future offline functionality)
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('Background sync triggered');
    // Handle background sync tasks here
  }
});

// Global error handler for service worker
self.addEventListener('error', event => {
  console.log('Service Worker error:', event.error);
});

// Unhandled promise rejection handler
self.addEventListener('unhandledrejection', event => {
  console.log('Service Worker unhandled promise rejection:', event.reason);
  event.preventDefault();
});