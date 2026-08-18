import os
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)
metadata = MetaData()
metadata.reflect(bind=engine)


        
FORBIDDEN_TABLES = {
    "admin",
    "adminpasswordreset",
    "site_settings",
    "contactmessage",   # PII: name/email/phone-in-message, no agent use case
    "subscriber",       # PII: mailing list emails, no agent use case
}

def get_table(table_name: str):
    """Fetch a reflected table object by name, e.g. get_table('order').

    Raises for any table in FORBIDDEN_TABLES even if it exists in the
    reflected schema — this is a hard block, not a convention.
    """
    if table_name in FORBIDDEN_TABLES:
        raise PermissionError(
            f"Table '{table_name}' is on the forbidden list and cannot "
            f"be accessed by the agent service."
        )
    if table_name not in metadata.tables:
        raise ValueError(
            f"Table '{table_name}' not found. Available tables: "
            f"{list(metadata.tables.keys())}"
        )
    return metadata.tables[table_name]

ALLOWED_COLUMNS = {
    "order": {
        "id",
        "orderRef",
        "firstName",
        "lastName",
        "email",
        "totalPrice",
        "notes",
        "orderStatus",
        "paymentMethod",
        "createdAt",
        # Deliberately excluded: phone, address, city, postalCode
    },
    "orderitem": {
        "id",
        "orderId",
        "productId",
        "quantity",
        "price",
        "customizations",
    },
    "product": {
        "id",
        "name",
        "description",
        "basePrice",
        "salePrice",
        "onSale",
        "isCustomizable",
        "hasPotOption",
        "hasColorOption",
        "hasFragranceOption",
        "hasWaxTypeOption",
        "stockQuantity",
        "createdAt",
    },
    "productcategory": {"productId", "categoryId"},
    "productimage": {"id", "productId", "imageUrl", "isPrimary"},
    "category": {"id", "name", "description", "parentId", "createdAt"},
    "candlecolor": {"id", "name", "hexCode"},
    "pot": {"id", "name", "description", "material"},
    "fragrance": {"id", "name", "description"},
    "waxtype": {"id", "name", "description"},
    "sale": {
        "id",
        "name",
        "subtitle",
        "heroImage",
        "startDate",
        "endDate",
        "isActive",
        "createdAt",
    },
    "saleproduct": {"saleId", "productId", "salePrice"},
}


def get_columns(table_name: str):
    """Return only the SQLAlchemy Column objects on the allowlist for this
    table, suitable for passing straight into select(*columns).

    Use this instead of get_table() + select(table) whenever the query
    result might be exposed to the LLM or the customer — it guarantees
    PII columns like phone/address/lastName never leave the database,
    regardless of what any tool function asks for.
    """
    table = get_table(table_name)  # still enforces FORBIDDEN_TABLES first

    if table_name not in ALLOWED_COLUMNS:
        raise PermissionError(
            f"Table '{table_name}' has no column allowlist defined — "
            f"refusing to expose any columns by default."
        )

    allowed = ALLOWED_COLUMNS[table_name]
    columns = [c for c in table.columns if c.name in allowed]

    missing = allowed - {c.name for c in table.columns}
    if missing:
        # Schema drift check: someone renamed a column in the DB but the
        # allowlist wasn't updated. Fail loud rather than silently
        # returning fewer columns than expected.
        raise RuntimeError(
            f"ALLOWED_COLUMNS for '{table_name}' references columns not "
            f"found in the actual schema: {missing}. Update the allowlist."
        )

    return columns




SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


