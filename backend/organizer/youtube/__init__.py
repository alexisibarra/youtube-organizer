"""YouTube gateway layer (AD-1).

Owns: every call to the YouTube Data API, and the translation of its quota and
error responses into this application's own error types.

Must never: import models or services. The gateway is a leaf — it maps the remote
API to plain data and knows nothing about how that data is stored or used.
"""
