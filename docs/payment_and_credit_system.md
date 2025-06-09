# Payment and Business Credit System Documentation

This document explains the core components and workflows of the payment and business credit system.

## Models

### Business

- Represents a business entity.
- Key field: `current_amount` (DecimalField) - Tracks the current credit/balance of the business.

### Account

- Represents a financial account (e.g., bank account, cash).
- Key field: `current_amount` (DecimalField) - Tracks the current balance of the account.

### BusinessCreditLog

- Records changes to a business's credit.
- Fields:
    - `business` (ForeignKey to Business)
    - `action` (CharField, choices: 'deposit', 'withdraw')
    - `amount` (DecimalField)
    - `remarks` (TextField)
    - `receipt` (FileField)
    - `created_by` (ForeignKey to UserBase)
- Signals update the related Business's `current_amount` on save and delete.

### Payment

- Records a payment transaction.
- Fields:
    - `invoice` (ForeignKey to Invoice, optional)
    - `purchase_bill` (ForeignKey to PurchaseBill, optional)
    - `expense` (ForeignKey to Expense, optional)
    - `amount` (DecimalField)
    - `related_business` (ForeignKey to Business, optional) - Automatically set based on linked Invoice/PurchaseBill. Required for 'from_business_credit' payments.
    - `related_account` (ForeignKey to Account, optional) - The account involved in the transaction.
    - `header` (CharField, choices: 'from_business_credit', 'fonepay', 'cash', 'transfer', 'card') - Payment method.
    - `action` (CharField, choices: 'deposit', 'withdraw') - Action from the perspective of the `related_account`.
    - `remarks` (CharField)
    - `receipt` (FileField)
    - `is_refunded` (BooleanField)
    - `created_by` (ForeignKey to UserBase)
- `clean` method validates that `related_business` is set for 'from_business_credit' payments and that the business has enough credit.
- `post_save` signal handles updates to `related_account.current_amount` for non-'from_business_credit' payments and creates/updates `BusinessCreditLog` entries for 'from_business_credit' payments.

## Relationships

- A `Payment` can be related to an `Invoice`, `PurchaseBill`, or `Expense`.
- A `Payment` can be associated with a `related_business` and a `related_account`.
- A `BusinessCreditLog` is associated with a `business`.
- `Payment`s with `header` 'from_business_credit' are linked to a `Business` via `related_business`, and their impact on business credit is managed through `BusinessCreditLog` entries created by the Payment's post-save signal.
- `Payment`s with other `header` types impact the `current_amount` of the `related_account`.

## APIs (Inferred)

Based on the file structure in `src/statements/apis/`, the following APIs are likely relevant:

- **Business APIs:**
    - `GET /api/statements/businesses/`: List businesses.
    - `GET /api/statements/businesses/{id}/`: Retrieve a business.
    - `POST /api/statements/businesses/`: Create a business.
    - `PUT /api/statements/businesses/{id}/`: Update a business.
    - `PATCH /api/statements/businesses/{id}/`: Partially update a business.
    - `DELETE /api/statements/businesses/{id}/`: Delete a business.

- **Account APIs:**
    - `GET /api/statements/accounts/`: List accounts.
    - `GET /api/statements/accounts/{id}/`: Retrieve an account.
    - `POST /api/statements/accounts/`: Create an account.
    - `PUT /api/statements/accounts/{id}/`: Update an account.
    - `PATCH /api/statements/accounts/{id}/`: Partially update an account.
    - `DELETE /api/statements/accounts/{id}/`: Delete an account.

- **Business Credit Log APIs:**
    - `GET /api/statements/business-credit-logs/`: List business credit logs.
    - `GET /api/statements/business-credit-logs/{id}/`: Retrieve a business credit log.
    - `POST /api/statements/business-credit-logs/`: Create a business credit log (for manual credit adjustments).
    - `PUT /api/statements/business-credit-logs/{id}/`: Update a business credit log.
    - `PATCH /api/statements/business-credit-logs/{id}/`: Partially update a business credit log.
    - `DELETE /api/statements/business-credit-logs/{id}/`: Delete a business credit log.

- **Payment APIs:**
    - `GET /api/statements/payments/`: List payments.
    - `GET /api/statements/payments/{id}/`: Retrieve a payment.
    - `POST /api/statements/payments/`: Create a payment.
    - `PUT /api/statements/payments/{id}/`: Update a payment.
    - `PATCH /api/statements/payments/{id}/`: Partially update a payment.
    - `DELETE /api/statements/payments/{id}/`: Delete a payment.

## Frontend Form Examples

Here are examples of how a frontend form for creating a Payment might look for different scenarios:

### Scenario 1: Paying an Invoice with Cash

- **Purpose:** Record a cash payment received for an invoice.
- **Relevant Models:** Payment, Invoice, Account (Cash Account)
- **Form Fields:**
    - `invoice`: Dropdown/Search to select the Invoice.
    - `amount`: Input field for the payment amount (should not exceed the remaining invoice amount).
    - `header`: Select 'cash'.
    - `action`: Select 'deposit' (from the perspective of the Cash Account).
    - `related_account`: Dropdown to select the Cash Account.
    - `remarks`: Textarea for optional remarks.
    - `receipt`: File upload for receipt (optional).

### Scenario 2: Paying a Purchase Bill using Business Credit

- **Purpose:** Record a payment made for a purchase bill using the business's credit.
- **Relevant Models:** Payment, PurchaseBill, Business, BusinessCreditLog
- **Form Fields:**
    - `purchase_bill`: Dropdown/Search to select the Purchase Bill.
    - `amount`: Input field for the payment amount (should not exceed the remaining purchase bill amount and the business's available credit).
    - `header`: Select 'from_business_credit'.
    - `related_business`: Dropdown/Search to select the Business (this field is required and validated).
    - `action`: This field might be hidden or automatically set to 'withdraw' as it's a withdrawal from business credit.
    - `remarks`: Textarea for optional remarks.
    - `receipt`: File upload for receipt (optional).

### Scenario 3: Recording an Expense Payment via Bank Transfer

- **Purpose:** Record a payment made for an expense using a bank account.
- **Relevant Models:** Payment, Expense, Account (Bank Account)
- **Form Fields:**
    - `expense`: Dropdown/Search to select the Expense.
    - `amount`: Input field for the payment amount (should not exceed the remaining expense amount).
    - `header`: Select 'transfer'.
    - `action`: Select 'withdraw' (from the perspective of the Bank Account).
    - `related_account`: Dropdown to select the Bank Account.
    - `remarks`: Textarea for optional remarks.
    - `receipt`: File upload for receipt (optional).

### Scenario 4: Manually Adjusting Business Credit (Deposit)

- **Purpose:** Manually add credit to a business's account (e.g., a refund received).
- **Relevant Models:** BusinessCreditLog, Business
- **Form Fields:**
    - `business`: Dropdown/Search to select the Business.
    - `action`: Select 'deposit'.
    - `amount`: Input field for the amount to deposit.
    - `remarks`: Textarea for remarks.
    - `receipt`: File upload for receipt (optional).
    - `created_by`: (Might be automatically set to the logged-in user).

### Scenario 5: Manually Adjusting Business Credit (Withdrawal)

- **Purpose:** Manually withdraw credit from a business's account (e.g., correcting an error).
- **Relevant Models:** BusinessCreditLog, Business
- **Form Fields:**
    - `business`: Dropdown/Search to select the Business.
    - `action`: Select 'withdraw'.
    - `amount`: Input field for the amount to withdraw (should not exceed the business's available credit - this validation would be in the `BusinessCreditLog` model's `clean` method or serializer).
    - `remarks`: Textarea for remarks.
    - `receipt`: File upload for receipt (optional).
    - `created_by`: (Might be automatically set to the logged-in user).

This document provides a comprehensive overview of the payment and business credit system, its components, relationships, likely API endpoints, and frontend form considerations for various scenarios.