# Scanner Workers

This service will execute authorized, non-destructive external checks in an isolated data plane.

Workers consume signed, versioned jobs; revalidate destinations; enforce time, size, redirect and concurrency limits; and emit immutable observations. They must not receive browser sessions, billing credentials or broad database access.
