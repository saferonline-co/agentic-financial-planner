"""Shared test setup.

The test suite runs against the stable, fictional fixture ``config.test.yaml``
(the ``config.skeleton.yaml`` template is intentionally incomplete, and ``config.example.yaml``
is a user-facing demo that may be edited freely). ``schema.load_config`` reads the
base file name from the ``FINMODEL_CONFIG`` env var, so point it here before any test
imports/loads a config.
"""
import os

os.environ.setdefault("FINMODEL_CONFIG", "config.test.yaml")
