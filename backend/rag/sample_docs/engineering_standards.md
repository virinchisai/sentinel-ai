# Engineering Standards

## Code Review
All production code changes require at least one approved review before merging.
Critical infrastructure changes (database migrations, auth, billing) require two
approvals, including one from a staff engineer or above.

## Testing Requirements
- Unit test coverage must be at least 80% for new modules
- Integration tests are required for all API endpoints
- Load tests are required before launching features expected to handle >1000 RPS

## Deployment
We use continuous deployment via GitHub Actions. Merges to `main` auto-deploy to
staging; production deploys require a manual approval gate. Rollbacks are automated
and triggered if error rate exceeds 1% within the first 10 minutes post-deploy.

## On-Call
Engineers rotate on-call weekly. On-call engineers must acknowledge pages within
15 minutes. Compensation is $500/week for on-call duty plus $200 per SEV1
incident handled outside business hours.
