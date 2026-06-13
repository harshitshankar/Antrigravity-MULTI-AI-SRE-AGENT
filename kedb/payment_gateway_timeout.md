# KEDB Entry: KEDB-0054

## Problem
External payment gateway timeout.

## Symptoms
- Payment transactions fail with HTTP 504 or Gateway Timeout status.
- Log entries containing:
  - `Stripe API request failed`
  - `api.stripe.com read timeout`
  - `Gateway timeout (504)`
- Elevated payment service error rates.

## Root Cause
Network routing issue or service outage on the external payment gateway provider's side (e.g., Stripe, PayPal).

## Resolution
1. **External Status Check**: Verify vendor status pages (e.g., `status.stripe.com`).
2. **Circuit Breaker**: Verify that the payment gateway circuit breaker has tripped to fail-fast and prevent blocking service threads.
3. **Failover Gateway**: Temporarily route new transactions to the secondary backup payment processor (e.g., Adyen/BrainTree).
4. **Retry Queue**: Ensure transactions are queued for asynchronous retry if applicable.
