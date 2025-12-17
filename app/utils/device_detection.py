"""
Device Detection Utility for UniPortal
Detects device type and screen size for optimal UI rendering
"""

import re
from flask import request

class DeviceDetector:
    def __init__(self):
        # Mobile device patterns
        self.mobile_patterns = [
            r'Mobile', r'Android', r'iPhone', r'iPad', r'iPod',
            r'BlackBerry', r'Windows Phone', r'Opera Mini',
            r'IEMobile', r'Mobile Safari'
        ]
        
        # Tablet patterns
        self.tablet_patterns = [
            r'iPad', r'Android.*Tablet', r'Kindle', r'Silk',
            r'PlayBook', r'Tablet'
        ]
        
        # Desktop patterns
        self.desktop_patterns = [
            r'Windows NT', r'Macintosh', r'Linux', r'X11'
        ]

    def get_user_agent(self):
        """Get user agent from request headers"""
        return request.headers.get('User-Agent', '')

    def is_mobile(self, user_agent=None):
        """Check if device is mobile"""
        if user_agent is None:
            user_agent = self.get_user_agent()
        
        # Check for mobile patterns
        for pattern in self.mobile_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                # Exclude tablets from mobile
                if not self.is_tablet(user_agent):
                    return True
        return False

    def is_tablet(self, user_agent=None):
        """Check if device is tablet"""
        if user_agent is None:
            user_agent = self.get_user_agent()
        
        for pattern in self.tablet_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        return False

    def is_desktop(self, user_agent=None):
        """Check if device is desktop"""
        if user_agent is None:
            user_agent = self.get_user_agent()
        
        # If not mobile or tablet, likely desktop
        if not self.is_mobile(user_agent) and not self.is_tablet(user_agent):
            return True
        return False

    def get_device_type(self, user_agent=None):
        """Get device type as string"""
        if user_agent is None:
            user_agent = self.get_user_agent()
        
        if self.is_mobile(user_agent):
            return 'mobile'
        elif self.is_tablet(user_agent):
            return 'tablet'
        else:
            return 'desktop'

    def get_device_info(self):
        """Get comprehensive device information"""
        user_agent = self.get_user_agent()
        device_type = self.get_device_type(user_agent)
        
        # Detect specific mobile OS
        mobile_os = None
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            mobile_os = 'ios'
        elif 'Android' in user_agent:
            mobile_os = 'android'
        elif 'Windows Phone' in user_agent:
            mobile_os = 'windows_phone'
        
        # Detect browser
        browser = 'unknown'
        if 'Chrome' in user_agent:
            browser = 'chrome'
        elif 'Firefox' in user_agent:
            browser = 'firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'safari'
        elif 'Edge' in user_agent:
            browser = 'edge'
        
        return {
            'device_type': device_type,
            'is_mobile': device_type == 'mobile',
            'is_tablet': device_type == 'tablet',
            'is_desktop': device_type == 'desktop',
            'mobile_os': mobile_os,
            'browser': browser,
            'user_agent': user_agent
        }

# Global instance
device_detector = DeviceDetector()