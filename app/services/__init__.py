"""Service layer: the business logic of the application.

Services know the domain rules, talk to the models and own the transaction.
They never import Flask: they raise domain exceptions and the HTTP layer turns
those into responses.
"""

from app.services import category_service, order_service, product_service

__all__ = ["category_service", "order_service", "product_service"]
