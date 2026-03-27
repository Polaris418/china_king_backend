from __future__ import annotations

from app.matcher import resolve_menu_item
from app.pricing import quote_order, validate_order


def main() -> None:
    print("resolve/general zo:", resolve_menu_item("general zo chicken"))
    print("resolve/low mein:", resolve_menu_item("low mein"))
    print(
        "validate:",
        validate_order(
            [{"item_name": "General Tso Chicken", "qty": 1, "size": "large"}],
            order_type="takeout",
            pickup_time="6:30 PM",
        ),
    )
    print(
        "quote:",
        quote_order(
            [{"item_name": "General Tso Chicken", "qty": 2, "size": "large"}],
            order_type="takeout",
            pickup_time="6:30 PM",
        ),
    )


if __name__ == "__main__":
    main()
