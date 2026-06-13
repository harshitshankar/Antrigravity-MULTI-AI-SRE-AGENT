# KEDB Entry: KEDB-0099

## Problem
API rate limit exceeded (HTTP 429).

## Symptoms
- Clients receive HTTP 429 Too Many Requests response code.
- Logs include:
  - `Rate limit exceeded`
  - `IP blocked by rate limiter`
  - `Request rejected: client exceeded quota`
- Metric graphs show spikes in requests per second.

## Root Cause
A surge in user traffic, a rogue client script scraping the site, or a DDoS attack targeting specific API routes.

## Resolution
1. **Identify IP**: Query ingress logs to identify the top requesting IP addresses or user accounts.
2. **Apply WAF Block**: Implement an IP rate limit or complete block on the Web Application Firewall (WAF) for the offending IP address.
3. **Adjust Quotas**: If the traffic is legitimate, increase rate limit quotas in API Gateway.
4. **Cache Responses**: Enable/increase caching at the CDN/gateway layer to reduce backend hits.
