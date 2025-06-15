Email Cleaner Application

The Email Cleaner is an intelligent email assistant designed to automatically organize, filter, and declutter your inbox, ensuring you never miss what matters. This application provides a user-friendly interface to manage your emails efficiently, including scanning, cleaning up, managing subscriptions, and scheduling automated cleanups.
Features

    User Authentication: Secure login using your email and a 16-character app password.
    Email Scanning:
        Scan your mailbox for unread, spam, and trash emails.
        Filter emails by various timeframes: last 7 days, 30 days, 90 days, 6 months, last year, or all emails.
        Option to include the Trash folder in the scan.
        View detailed scan results, including counts for unread, spam, and trash emails.
        Sort scanned emails by date, sender, or subject.
    Email Cleanup Settings:
        Choose your preferred delete mode: "Move to Trash (Recommended)" or "Permanent Delete".
        Option to include emails from the Trash folder during a scan for cleanup.
    Subscription Management:
        Identify and list email subscriptions from your inbox.
        Unsubscribe from unwanted email subscriptions directly through the application. Supports both HTTP and Mailto unsubscribe links.
    Scheduled Cleanups:
        Enable and configure automated email cleanup tasks.
        Set cleanup frequency: every day, every Monday, every 1st of the month, or custom selected days.
        Specify a daily time for the cleanup to run.
        Option to run a one-time cleanup on a specific date and time.
        Select types of emails to clean: unread older than 7 days, read older than 30 days, subscription emails, spam, and trash.
    Dashboard: A centralized dashboard to navigate to different functionalities like Clean Up Settings, Scan Email, and Delete Subscriptions.

Technologies Used

    Python
    Streamlit (for the web interface)
    IMAPLib (for email interaction)
    email module (for email parsing)
    BeautifulSoup (for parsing HTML to extract unsubscribe links)

Setup and Installation

    Clone the Repository:
    Bash

git clone <repository_url>
cd email-cleaner-app

Install Dependencies:
Bash

pip install -r requirements.txt

(Note: A requirements.txt file is assumed to exist with streamlit, imaplib, beautifulsoup4, and pytz.)
Set up an App Password for Gmail (if using Gmail):

    Go to your Google Account.
    Navigate to Security.
    Under "How you sign in to Google," select "2-Step Verification." (If you don't have it enabled, you'll need to enable it).
    Scroll down and select "App passwords."
    Select "Mail" as the app and "Other (Custom name)" for the device.
    Generate the 16-character password. This is the password you will use to log in to the application.

Run the Application:
Bash

    streamlit run Main.py

    This will open the application in your web browser.

Usage

    Login: On the login page, enter your email address and the 16-character app password.
    Dashboard: After successful login, you will be directed to the dashboard where you can access various features.
    Scan Emails: Click "Scan Mailbox" to view and manage your unread, spam, and trash emails. You can configure scan settings such as the time range and inclusion of the Trash folder.
    Clean Up Settings: Adjust your email deletion preferences (move to trash or permanent delete) and decide whether to include the Trash folder in scans.
    Delete Subscriptions: Access this section to see a list of your email subscriptions and unsubscribe from them.
    Schedule Clean Up: Configure automated cleanup tasks, setting the frequency, time, and types of emails to be cleaned.

Project Structure

    Main.py: Application entry point and login interface.
    Dashboard.py: Main navigation and user dashboard.
    CleanUpSettings.py: Streamlit page for configuring email cleanup preferences.
    ScanEmails.py: Streamlit page for scanning and viewing email categories (unread, spam, trash).
    DeleteSubscriptions.py: Streamlit page for managing and unsubscribing from email lists.
    ScheduleCleanUp.py: Streamlit page for setting up recurring email cleanup schedules.
    run_scheduled_cleanup.py: Script responsible for executing the configured scheduled cleanup tasks.
    util.py: Contains helper functions for login, session management, CSS loading, background images, and unsubscribe link extraction.
    utilClean.py: Contains core logic for IMAP connection, email scanning, parsing, and deletion operations.
    assets/: Directory for static assets like CSS files and images.
    config/: Directory to store user-specific schedule configurations (created automatically).
    storage/unsubscribed/: Directory to store records of unsubscribed emails (created automatically).
