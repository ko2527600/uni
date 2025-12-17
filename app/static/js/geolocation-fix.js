/**
 * Enhanced Geolocation Handler
 * Fixes common location permission issues and provides better user experience
 */

class GeolocationHandler {
    constructor() {
        this.isHTTPS = location.protocol === 'https:';
        this.isLocalhost = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
        this.init();
    }

    init() {
        // Check if geolocation is supported
        if (!navigator.geolocation) {
            console.error('Geolocation is not supported by this browser');
            return false;
        }

        // Check if we're on HTTPS or localhost (required for geolocation)
        if (!this.isHTTPS && !this.isLocalhost) {
            console.warn('Geolocation requires HTTPS or localhost');
        }

        return true;
    }

    async requestLocation(options = {}) {
        const defaultOptions = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
        };

        const finalOptions = { ...defaultOptions, ...options };

        return new Promise((resolve, reject) => {
            // First, check permissions API if available
            if ('permissions' in navigator) {
                navigator.permissions.query({ name: 'geolocation' }).then((result) => {
                    console.log('Geolocation permission status:', result.state);
                    
                    if (result.state === 'denied') {
                        reject({
                            code: 1,
                            message: 'Location permission denied. Please reset permissions and try again.',
                            type: 'PERMISSION_DENIED'
                        });
                        return;
                    }
                    
                    // Proceed with geolocation request
                    this.getCurrentPosition(resolve, reject, finalOptions);
                }).catch(() => {
                    // Fallback if permissions API not supported
                    this.getCurrentPosition(resolve, reject, finalOptions);
                });
            } else {
                // Fallback if permissions API not supported
                this.getCurrentPosition(resolve, reject, finalOptions);
            }
        });
    }

    getCurrentPosition(resolve, reject, options) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('Location obtained:', position.coords);
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: position.timestamp
                });
            },
            (error) => {
                console.error('Geolocation error:', error);
                
                let errorMessage = '';
                let errorType = '';
                
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorType = 'PERMISSION_DENIED';
                        if (!this.isHTTPS && !this.isLocalhost) {
                            errorMessage = 'Location access requires HTTPS. Please use a secure connection.';
                        } else {
                            errorMessage = 'Location permission denied. Please check your browser settings and allow location access for this site.';
                        }
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorType = 'POSITION_UNAVAILABLE';
                        errorMessage = 'Location information is unavailable. Please check your GPS/location services.';
                        break;
                    case error.TIMEOUT:
                        errorType = 'TIMEOUT';
                        errorMessage = 'Location request timed out. Please try again.';
                        break;
                    default:
                        errorType = 'UNKNOWN_ERROR';
                        errorMessage = 'An unknown error occurred while retrieving location.';
                        break;
                }
                
                reject({
                    code: error.code,
                    message: errorMessage,
                    type: errorType,
                    originalError: error
                });
            },
            options
        );
    }

    // Helper method to show user-friendly instructions
    getPermissionInstructions() {
        const userAgent = navigator.userAgent;
        let instructions = '';

        if (userAgent.includes('Chrome')) {
            instructions = `
                <strong>Chrome Instructions:</strong><br>
                1. Click the location icon (🌐) in the address bar<br>
                2. Select "Always allow" for location access<br>
                3. Refresh the page and try again
            `;
        } else if (userAgent.includes('Firefox')) {
            instructions = `
                <strong>Firefox Instructions:</strong><br>
                1. Click the shield icon in the address bar<br>
                2. Click "Allow" for location access<br>
                3. Refresh the page and try again
            `;
        } else if (userAgent.includes('Safari')) {
            instructions = `
                <strong>Safari Instructions:</strong><br>
                1. Go to Safari > Preferences > Websites > Location<br>
                2. Set this website to "Allow"<br>
                3. Refresh the page and try again
            `;
        } else if (userAgent.includes('Edge')) {
            instructions = `
                <strong>Edge Instructions:</strong><br>
                1. Click the location icon in the address bar<br>
                2. Select "Allow" for location access<br>
                3. Refresh the page and try again
            `;
        } else {
            instructions = `
                <strong>General Instructions:</strong><br>
                1. Look for a location/GPS icon in your browser's address bar<br>
                2. Click it and select "Allow" or "Always allow"<br>
                3. Refresh the page and try again
            `;
        }

        return instructions;
    }

    // Method to check if location services are enabled
    async checkLocationServices() {
        try {
            const position = await this.requestLocation({ timeout: 5000 });
            return { enabled: true, position };
        } catch (error) {
            return { enabled: false, error };
        }
    }
}

// Global function for attendance system
async function startAttendanceWithLocation(formId, statusElementId) {
    const locationStatus = document.getElementById(statusElementId);
    const form = document.getElementById(formId);
    
    if (!locationStatus || !form) {
        console.error('Required elements not found');
        return;
    }

    const geoHandler = new GeolocationHandler();
    
    // Update status
    locationStatus.style.background = 'rgba(59, 130, 246, 0.2)';
    locationStatus.style.border = '1px solid rgba(59, 130, 246, 0.4)';
    locationStatus.style.color = 'white';
    locationStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting your location...';

    try {
        const location = await geoHandler.requestLocation();
        
        // Set location values
        const latInput = form.querySelector('input[name*="latitude"], input[id*="Latitude"]');
        const lngInput = form.querySelector('input[name*="longitude"], input[id*="Longitude"]');
        
        if (latInput) latInput.value = location.latitude;
        if (lngInput) lngInput.value = location.longitude;
        
        // Success status
        locationStatus.style.background = 'rgba(34, 197, 94, 0.2)';
        locationStatus.style.border = '1px solid rgba(34, 197, 94, 0.4)';
        locationStatus.innerHTML = '✅ Location captured! Starting session...';
        
        // Submit form after short delay
        setTimeout(() => {
            form.submit();
        }, 500);
        
    } catch (error) {
        // Error status
        locationStatus.style.background = 'rgba(239, 68, 68, 0.2)';
        locationStatus.style.border = '1px solid rgba(239, 68, 68, 0.4)';
        
        let errorHTML = `❌ ${error.message}`;
        
        if (error.type === 'PERMISSION_DENIED') {
            errorHTML += `
                <div style="margin-top: 10px; font-size: 12px; line-height: 1.4;">
                    ${geoHandler.getPermissionInstructions()}
                </div>
            `;
        }
        
        locationStatus.innerHTML = errorHTML;
        
        console.error('Location error:', error);
    }
}

// Initialize geolocation handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.geoHandler = new GeolocationHandler();
    
    // Make functions globally available
    window.startAttendanceWithLocation = startAttendanceWithLocation;
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GeolocationHandler;
}