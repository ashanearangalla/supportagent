import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_columns, get_table
from ..schemas import OrderDetail, OrderItemDetail, ProductOption

# Maps a key that might appear inside orderitem.customizations JSON to the
# lookup table it references. This mapping is application knowledge — it
# doesn't exist as a real foreign key in the schema, so it has to live in
# code. Extend this if the store adds new customizable option types.
CUSTOMIZATION_LOOKUP_TABLES = {
    "fragrance": "fragrance",
    "color": "candlecolor",
    "pot": "pot",
    "waxType": "waxtype",
}

def _resolve_option(db: Session, option_type: str, option_id: int) -> ProductOption | None:
    """Look up a single customization option's display name by id."""
    table_name = CUSTOMIZATION_LOOKUP_TABLES.get(option_type)
    if not table_name:
        return None

    columns = get_columns(table_name)
    table = get_table(table_name)
    stmt = select(*columns).where(table.c.id == option_id)
    row = db.execute(stmt).mappings().first()
    if not row:
        return None

    return ProductOption(id=row["id"], name=row["name"])




def get_order_detail(db: Session, order_id: int) -> OrderDetail | None:
    """Fetch an order plus its items, with customizations resolved into
    readable names instead of raw JSON with bare ids."""
    
    order_table = get_table("order")
    order_columns = get_columns("order")
    order_stmt = select(*order_columns).where(order_table.c.id == order_id)
    order_row = db.execute(order_stmt).mappings().first()
    
    if not order_row:
        return None

    item_table = get_table("orderitem")
    item_columns = get_columns("orderitem")
    items_stmt = select(*item_columns).where(item_table.c.orderId == order_id)
    item_rows = db.execute(items_stmt).mappings().all()
    
    product_table = get_table("product")
    product_columns = get_columns("product")
    
    items: list[OrderItemDetail] = []
    
    for item in item_rows:
        prod_stmt = select(*product_columns).where(product_table.c.id == item["productId"])
        product_row = db.execute(prod_stmt).mappings().first()
        
        customizations = {}
        raw = item.get("customizations")
        
        if raw:
            try:
                parsed = json.loads(raw)
                # Some rows store customizations as an empty JSON array
                # ([]) rather than an object ({}) when nothing was
                # customized — only treat it as a dict if it actually is one.
                if isinstance(parsed, dict):
                    customizations = parsed
            except (json.JSONDecodeError, TypeError):
                customizations = {}
                
        resolved: dict[str, ProductOption | None] = {}
        for key, value in customizations.items():
            if isinstance(value, dict) and "id" in value:
                resolved[key] = _resolve_option(db, key, int(value["id"]))
                
        items.append(
            OrderItemDetail(
                id=item["id"],
                productId=item["productId"],
                productName=product_row["name"] if product_row else "Unknown product",
                quantity=item["quantity"],
                price=item["price"],
                fragrance=resolved.get("fragrance"),
                color=resolved.get("color"),
                pot=resolved.get("pot"),
                waxType=resolved.get("waxType"),
            )
        )
        
    return OrderDetail(
        id=order_row["id"],
        orderRef=order_row["orderRef"],
        firstName=order_row["firstName"],
        lastName=order_row["lastName"],
        email=order_row["email"],
        totalPrice=order_row["totalPrice"],
        orderStatus=order_row["orderStatus"],
        paymentMethod=order_row["paymentMethod"],
        createdAt=str(order_row["createdAt"]),
        notes=order_row.get("notes"),
        items=items,
    )