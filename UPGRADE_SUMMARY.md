UPDATED IMPLEMENTATION PLAN
Phase 1: Core Enforcement (Now)
Create @premium_required decorator
Apply to critical routes (upload, download, grade, forum)
Add subscription status banners
Lock UI elements when expired
Show "🔒 Premium Required" messages
Phase 2: Payment Integration (Later)
Integrate Paystack API
Create payment flow:
Rep selects plan (Semester/Year/4-Year)
Redirects to Paystack checkout
Webhook handles payment confirmation
Auto-extends premium_expiry date
Add payment history tracking
Email receipts
Phase 3: Notifications & Polish (Later)
Email reminders (7 days, 3 days, expiry)
In-app countdown timers
Grace period logic (optional)
Analytics dashboard for reps
🎯 WHAT TO BUILD NOW
Since we're holding payment integration for later, let's focus on:

Subscription enforcement - Lock features when expired
UI updates - Show premium status and locked features
Manual activation - Admin can manually extend subscriptions for testing
Subscription page - Show pricing (even if payment isn't live yet)