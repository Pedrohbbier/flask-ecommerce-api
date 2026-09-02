"""Order routes.

Prefix: /api/v1/orders
"""

from app.api.v1.blueprints import orders_blp as blp
from app.controllers.order_controller import (
    OrderCollectionController,
    OrderController,
    OrderItemCollectionController,
    OrderItemController,
)

blp.route("")(OrderCollectionController)
blp.route("/<int:order_id>")(OrderController)
blp.route("/<int:order_id>/items")(OrderItemCollectionController)
blp.route("/<int:order_id>/items/<int:item_id>")(OrderItemController)
