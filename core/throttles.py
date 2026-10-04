"""Throttle class sets.

Rates live in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] and can be
tuned per environment through THROTTLE_* environment variables. Sensitive views
set ``throttle_scope`` and use ``SCOPED_THROTTLES`` so the scope limit applies
on top of the global anon/user limits.
"""

from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

SCOPED_THROTTLES = [ScopedRateThrottle, AnonRateThrottle, UserRateThrottle]
