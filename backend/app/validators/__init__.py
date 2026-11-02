"""Validation of client input, written as plain Python checks.

Each validator returns either clean, typed values or a Failure, which the router turns
into 422 {"error": {"code": "validation_error", ...}}.
"""
