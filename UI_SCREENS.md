# UI Screens for ERP System

This document outlines the necessary UI screens and sections to support the functionalities discussed for Subdomains, Email Templates, and Subscriptions.

## 1. Subdomains

### 1.1 School Settings / Profile Page
*   **Purpose:** Allows school administrators to view and update their school's subdomain.
*   **Key Elements:**
    *   Current subdomain display.
    *   Input field for new subdomain.
    *   "Check Availability" button/feature.
    *   "Suggest Subdomain" button/feature.
    *   Save/Update button.
    *   Validation messages for subdomain availability and format.

### 1.2 Subdomain Availability Checker (Integrated)
*   **Purpose:** Provides real-time feedback on subdomain availability during input.
*   **Key Elements:**
    *   Indicator (e.g., green check, red X) next to the subdomain input field.
    *   Text message indicating availability or reason for unavailability.

### 1.3 Subdomain Suggestion (Integrated)
*   **Purpose:** Offers alternative subdomain suggestions if the desired one is taken.
*   **Key Elements:**
    *   List of suggested subdomains, possibly clickable to auto-fill the input.

## 2. Email Templates

### 2.1 Email Template Management (List, Create, Edit, Delete)
*   **Purpose:** Centralized interface for super administrators to manage all email templates.
*   **Key Elements:**
    *   **List View:** Table or list of all templates with columns like Name, Subject, Type, Status (Active/Inactive), Last Updated.
    *   Search/Filter options (by name, type, status).
    *   "Create New Template" button.
    *   Actions for each template: View Details, Edit, Delete (soft delete), Preview, Send Test.
    *   Pagination.
*   **Create/Edit Form:**
    *   Fields for Template Name, Subject, Body (rich text editor recommended).
    *   Dropdown for Template Type (e.g., Trial Started, Password Reset, Custom).
    *   Toggle for Is Active.
    *   Display of available variables for the selected template type.
    *   Save/Cancel buttons.

### 2.2 Email Template Preview
*   **Purpose:** Allows users to see how a template will render with specific variable values.
*   **Key Elements:**
    *   Input fields for each variable defined in the template.
    *   "Preview" button.
    *   Rendered email subject and body display.

### 2.3 Test Email Sender
*   **Purpose:** Enables sending a test email to a specified recipient using a selected template and variables.
*   **Key Elements:**
    *   Dropdown to select an existing template.
    *   Input field for recipient email address.
    *   Input fields for template variables.
    *   "Send Test Email" button.
    *   Success/Error messages.

### 2.4 Custom Email Sender
*   **Purpose:** Allows sending one-off emails without using a predefined template.
*   **Key Elements:**
    *   Input fields for Recipient(s), CC, BCC, Subject, Body (rich text editor).
    *   Option to add attachments.
    *   "Send Email" button.
    *   Success/Error messages.

### 2.5 Sent Email Log
*   **Purpose:** Displays a log of all emails sent by the system.
*   **Key Elements:**
    *   Table or list of sent emails with columns like Recipient, Subject, Template (if applicable), Status (Sent, Delivered, Failed, Bounced), Sent At.
    *   Search/Filter options (by recipient, template, status, date range).
    *   Pagination.
    *   Clickable rows to view Sent Email Detail.

### 2.6 Sent Email Detail
*   **Purpose:** Shows the full content and metadata of a specific sent email.
*   **Key Elements:**
    *   Recipient, Subject, Body (rendered).
    *   Status, Sent At, Delivered At, Error Message (if any).
    *   Associated Template (link to template details).
    *   Any additional metadata.

## 3. Subscriptions

### 3.1 Subscription Plan Management (Super Admin)
*   **Purpose:** Allows super administrators to create, view, edit, and delete subscription plans.
*   **Key Elements:**
    *   **List View:** Table of all subscription plans with columns like Name, Monthly Price, Yearly Price, Max Students, Max Teachers, Features, Status (Active/Inactive).
    *   "Create New Plan" button.
    *   Actions for each plan: View Details, Edit, Delete (soft delete).
*   **Create/Edit Form:**
    *   Fields for Plan Name, Description, Monthly Price, Yearly Price.
    *   Input fields for Max Students, Max Teachers, Max Storage.
    *   Dynamic fields for additional Features (key-value pairs).
    *   Toggle for Is Active, Is Default.
    *   Save/Cancel buttons.

### 3.2 School Subscription Status / Dashboard
*   **Purpose:** For school administrators to view their current subscription status and usage.
*   **Key Elements:**
    *   Current Plan Name.
    *   Subscription Status (Active, Trialing, Expired, etc.).
    *   Start Date, End Date, Days Remaining.
    *   Usage Metrics: Current Students vs. Max Students, Current Teachers vs. Max Teachers, Current Storage vs. Max Storage.
    *   "Upgrade Plan" / "Manage Subscription" button (links to checkout/management flow).
    *   "View Payment History" button.

### 3.3 Subscription Checkout / Upgrade / Downgrade Flow
*   **Purpose:** Guides users through selecting a plan and making a payment.
*   **Key Elements:**
    *   List of available subscription plans with details (features, pricing).
    *   Option to choose billing cycle (monthly/yearly).
    *   Payment method selection (e.g., Paystack integration).
    *   Confirmation and payment processing steps.
    *   For upgrades/downgrades: display of prorated costs/credits.

### 3.4 Payment History
*   **Purpose:** Displays a list of past payments and invoices for a school.
*   **Key Elements:**
    *   Table with columns like Date, Amount, Plan, Status (Paid, Failed), Transaction ID.
    *   Option to view/download invoices.

### 3.5 Usage Tracking Dashboard
*   **Purpose:** Provides a visual overview of resource consumption against subscription limits.
*   **Key Elements:**
    *   Graphs/charts for student, teacher, and storage usage over time.
    *   Alerts for approaching or exceeded limits.

### 3.6 Dunning Management (Admin)
*   **Purpose:** For super administrators to manage and monitor failed payments and subscription recovery.
*   **Key Elements:**
    *   List of subscriptions with failed payments.
    *   Status of dunning attempts.
    *   Option to manually trigger dunning emails or update subscription status.
