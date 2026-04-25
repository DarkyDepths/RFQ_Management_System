"""
Translators package — conversion between Pydantic schemas and SQLAlchemy models.

Each file provides to_model() and to_schema() functions for one resource.
Keeps serialization logic out of controllers and routes.
"""
