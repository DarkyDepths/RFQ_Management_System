"""
Datasources package — pure database queries using SQLAlchemy sessions.

Each file contains a datasource class for one API resource.
Datasources only perform CRUD operations — no business logic.
They receive a SQLAlchemy Session and return model instances or lists.
"""
