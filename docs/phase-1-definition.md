# Beavelo v1 — Product Definition

## User
A business user who needs answers from the existing sales database but does not know SQL.

## Core job
Convert a natural-language business question into a safe, read-only SQL query and return understandable results.

## In scope
- Existing MySQL database
- Customers, suppliers, products, orders, and order_details
- Natural-language questions
- Clarification for ambiguous requests
- Read-only SELECT queries
- Results table and optional SQL visibility

## Out of scope
- User-uploaded files
- Google Sheets
- Authentication
- Charts and dashboards
- Writes, updates, deletes, or schema changes

## Success criteria
- At least 80% of evaluation questions generate executable SQL.
- No non-SELECT statement reaches the database.
- Ambiguous questions request clarification.
- Typical response completes within 10 seconds.