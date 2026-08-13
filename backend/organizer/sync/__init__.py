"""Sync layer (AD-1).

Owns: sync runs, the outbox drain, and quota handling. The only caller of the
gateway's write methods (AD-6).

Must never: be reachable from a request thread. Sync work is triggered by a
management command, never inline from an API view.
"""
