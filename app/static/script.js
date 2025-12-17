/* UniPortal - Centralized JavaScript */

// ========== AUTO-DISMISS FLASH MESSAGES ==========
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-msg');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.classList.add('fade-out');
            setTimeout(function() {
                flash.remove();
            }, 500); // Wait for fade animation to complete
        }, 3000);
    });
});

// ========== MOBILE SIDEBAR TOGGLE ==========
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const body = document.body;
    
    if (sidebar) {
        sidebar.classList.toggle('mobile-active');
        body.classList.toggle('menu-open');
    }
}

// Close sidebar when clicking outside on mobile (on overlay)
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('mobileMenuToggle');
    const body = document.body;
    
    if (sidebar && toggle && window.innerWidth <= 768) {
        // Check if click is on the overlay (outside sidebar and toggle)
        if (!sidebar.contains(event.target) && !toggle.contains(event.target) && body.classList.contains('menu-open')) {
            sidebar.classList.remove('mobile-active');
            body.classList.remove('menu-open');
        }
    }
});

// ========== SIDEBAR TOGGLE (Multi-View Navigation) ==========
function showView(viewName) {
    // Close mobile sidebar when view is selected
    if (window.innerWidth <= 768) {
        const sidebar = document.getElementById('sidebar');
        const body = document.body;
        if (sidebar) {
            sidebar.classList.remove('mobile-active');
            body.classList.remove('menu-open');
        }
    }

    // Hide all views
    document.querySelectorAll('.view-section').forEach(view => {
        view.classList.remove('active');
    });

    // Show selected view
    const targetView = document.getElementById(viewName + 'View');
    if (targetView) {
        targetView.classList.add('active');
    }

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to clicked nav item
    if (event && event.target) {
        const navItem = event.target.closest('.nav-item');
        if (navItem) {
            navItem.classList.add('active');
        }
    }
}

// ========== GRADE ASSIGNMENT MODAL ==========
function gradeAssignment(assignmentId, studentName, filename) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
    
    modal.innerHTML = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; width: 90%; max-width: 500px; box-shadow: 0 10px 40px rgba(0,0,0,0.3);">
            <h2 style="color: white; margin-bottom: 10px;">Grade Assignment</h2>
            <p style="color: rgba(255,255,255,0.8); margin-bottom: 20px; font-size: 14px;">Student: ${studentName}<br>File: ${filename}</p>
            <form method="POST" action="/grade_assignment/${assignmentId}">
                <div style="margin-bottom: 15px;">
                    <label style="color: white; display: block; margin-bottom: 5px; font-size: 14px;">Grade *</label>
                    <input type="text" name="grade" placeholder="e.g., A, B+, 85" required 
                        style="width: 100%; padding: 10px; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.2); color: white; font-size: 14px;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="color: white; display: block; margin-bottom: 5px; font-size: 14px;">Feedback (Optional)</label>
                    <textarea name="feedback" rows="3" placeholder="Enter feedback for the student..."
                        style="width: 100%; padding: 10px; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.2); color: white; font-size: 14px; resize: vertical;"></textarea>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" style="flex: 1; padding: 12px; background: rgba(34,197,94,0.8); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">
                        Submit Grade
                    </button>
                    <button type="button" onclick="this.closest('div').parentElement.parentElement.remove()" 
                        style="flex: 1; padding: 12px; background: rgba(239,68,68,0.8); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    setTimeout(() => modal.querySelector('input[name="grade"]').focus(), 100);
}


// ========== LOGOUT CONFIRMATION ==========
function confirmLogout(event) {
    event.preventDefault();
    
    const confirmed = confirm('Are you sure you want to logout?');
    
    if (confirmed) {
        window.location.href = event.target.href || event.currentTarget.href;
    }
    
    return false;
}
