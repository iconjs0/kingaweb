# Scanner Workers

This service will execute authorized, non-destructive external checks in an isolated data plane.

Workers consume signed, versioned jobs; revalidate destinations; enforce time, size, redirect and concurrency limits; and emit immutable observations. They must not receive browser sessions, billing credentials or broad database access.

The first vertical slice currently runs through the control-plane API while the isolated worker boundary is built. It is deliberately limited to verified hostnames, HTTPS root responses, public destinations, six-second requests and zero redirects. The worker extraction milestone will preserve these controls while moving execution out of the API process.
