# Data Validation Report

**Generated:** 2024-04-13 10:01:53 UTC  
**Local Time:** 2024-04-13 15:31:53  
**Report Version:** 1.0  
**Generator:** policy-dq-validator  
**Input File:** sample_data/customers_with_issues.csv  
**Rules Source:** customer_data

## Summary

🔴 **Overall Status:** 🚨 **CRITICAL ISSUES**

| Metric | Value |
|--------|-------|
| Total Records | 20 |
| Total Rules | 10 |
| Total Validations | 200 |
| Passed Validations | 111 |
| Failed Validations | 89 |
| Success Rate | 55.5% |

## Severity Breakdown

| Severity | Count |
|----------|-------|
| 🚨 Critical | 40 |
| ❌ Error | 100 |
| ⚠️ Warning | 60 |
| ℹ️ Info | 0 |

## Statistics

### Top Failed Rules

| Rule | Failures |
|----|----------|
| `first_name_required` | 20 |
| `last_name_required` | 20 |
| `phone_format` | 20 |
| `registration_date_type` | 20 |
| `age_range_check` | 3 |

### Top Failed Fields

| Field | Failures |
|-----|----------|
| `first_name` | 20 |
| `last_name` | 20 |
| `phone` | 20 |
| `registration_date` | 20 |
| `customer_id` | 3 |

## Detailed Failures

### 🚨 Critical Issues (3 issues)

#### Rule: `customer_id_required`

| Row | Field | Message |
|-----|-------|---------|
| 16 | `customer_id` | Required field 'customer_id' is empty |
#### Rule: `customer_id_unique`

| Row | Field | Message |
|-----|-------|---------|
| 1 | `customer_id` | Field 'customer_id' value 'CUST001' is not unique (duplicate found) |
| 11 | `customer_id` | Field 'customer_id' value 'CUST001' is not unique (duplicate found) |

### ❌ Errors (63 issues)

#### Rule: `first_name_required`

| Row | Field | Message |
|-----|-------|---------|
| 1 | `first_name` | Required field 'first_name' is missing |
| 2 | `first_name` | Required field 'first_name' is missing |
| 3 | `first_name` | Required field 'first_name' is missing |
| 4 | `first_name` | Required field 'first_name' is missing |
| 5 | `first_name` | Required field 'first_name' is missing |
| 6 | `first_name` | Required field 'first_name' is missing |
| 7 | `first_name` | Required field 'first_name' is missing |
| 8 | `first_name` | Required field 'first_name' is missing |
| 9 | `first_name` | Required field 'first_name' is missing |
| 10 | `first_name` | Required field 'first_name' is missing |

*... and 10 more similar failures*
#### Rule: `last_name_required`

| Row | Field | Message |
|-----|-------|---------|
| 1 | `last_name` | Required field 'last_name' is missing |
| 2 | `last_name` | Required field 'last_name' is missing |
| 3 | `last_name` | Required field 'last_name' is missing |
| 4 | `last_name` | Required field 'last_name' is missing |
| 5 | `last_name` | Required field 'last_name' is missing |
| 6 | `last_name` | Required field 'last_name' is missing |
| 7 | `last_name` | Required field 'last_name' is missing |
| 8 | `last_name` | Required field 'last_name' is missing |
| 9 | `last_name` | Required field 'last_name' is missing |
| 10 | `last_name` | Required field 'last_name' is missing |

*... and 10 more similar failures*
#### Rule: `email_required`

| Row | Field | Message |
|-----|-------|---------|
| 12 | `email` | Required field 'email' is empty |
#### Rule: `email_format_check`

| Row | Field | Message |
|-----|-------|---------|
| 8 | `email` | Field 'email' value 'invalid-email-format' does not match pattern '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' |
| 12 | `email` | Field 'email' value '' does not match pattern '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' |
#### Rule: `registration_date_type`

| Row | Field | Message |
|-----|-------|---------|
| 1 | `registration_date` | Field 'registration_date' is missing for type check |
| 2 | `registration_date` | Field 'registration_date' is missing for type check |
| 3 | `registration_date` | Field 'registration_date' is missing for type check |
| 4 | `registration_date` | Field 'registration_date' is missing for type check |
| 5 | `registration_date` | Field 'registration_date' is missing for type check |
| 6 | `registration_date` | Field 'registration_date' is missing for type check |
| 7 | `registration_date` | Field 'registration_date' is missing for type check |
| 8 | `registration_date` | Field 'registration_date' is missing for type check |
| 9 | `registration_date` | Field 'registration_date' is missing for type check |
| 10 | `registration_date` | Field 'registration_date' is missing for type check |

*... and 10 more similar failures*

### ⚠️ Warnings (23 issues)

#### Rule: `phone_format`

| Row | Field | Message |
|-----|-------|---------|
| 1 | `phone` | Field 'phone' value '555-0101' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 2 | `phone` | Field 'phone' value '555-0102' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 3 | `phone` | Field 'phone' value '555-0103' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 4 | `phone` | Field 'phone' value '555-0104' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 5 | `phone` | Field 'phone' value '555-0105' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 6 | `phone` | Field 'phone' value '555-0106' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 7 | `phone` | Field 'phone' value '555-0107' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 8 | `phone` | Field 'phone' value '555-0108' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 9 | `phone` | Field 'phone' value '555-0109' does not match pattern '^\+?[1-9]\d{1,14}$' |
| 10 | `phone` | Field 'phone' value '555-0110' does not match pattern '^\+?[1-9]\d{1,14}$' |

*... and 10 more similar failures*
#### Rule: `age_range_check`

| Row | Field | Message |
|-----|-------|---------|
| 7 | `age` | Field 'age' value 'invalid_age' cannot be converted to number: Cannot convert 'invalid_age' to number |
| 9 | `age` | Field 'age' numeric range validation failed: value 17 is less than minimum 18 |
| 10 | `age` | Field 'age' numeric range validation failed: value 105 is greater than maximum 99 |

---

*Report generated by policy-dq-validator*