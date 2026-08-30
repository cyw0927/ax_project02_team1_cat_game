import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.main import app
from app.users.models import User


def build_user(*, soft_balance=1000):
    return User(
        id=uuid.uuid4(),
        external_student_id=f"SHOP-{uuid.uuid4()}",
        username="상점 테스트 사용자",
        role="USER",
        soft_balance=soft_balance,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


def build_item():
    return Item(id=4, category="FURNITURE", name="학습용 책상", price=600)


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class Scalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class ShopSession:
    def __init__(self, user, item):
        self.user = user
        self.item = item
        self.inventory = None
        self.replayed = None
        self.added = None
        self.committed = False
        self.rolled_back = False
        self.fail_commit = False
        self.inventory_rows = []

    def get(self, model, identity, **kwargs):
        if model is User and identity == self.user.id:
            return self.user
        if model is Item and self.item is not None and identity == self.item.id:
            return self.item
        return None

    def scalar(self, statement):
        statement_text = str(statement)
        if "inventories.last_purchase_request_id =" in statement_text:
            return self.replayed
        return self.inventory

    def scalars(self, statement):
        return Scalars([] if self.item is None else [self.item])

    def execute(self, statement):
        return Rows(self.inventory_rows)

    def add(self, inventory):
        self.inventory = inventory
        self.added = inventory

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def request(db, method, path, json=None):
    def override_get_db():
        yield db

    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(
                method,
                path,
                headers={"X-User-ID": str(db.user.id)},
                json=json,
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(send())
    finally:
        app.dependency_overrides.clear()


def purchase_payload(item_id=4, request_id=None):
    return {
        "item_id": item_id,
        "purchase_request_id": str(request_id or uuid.uuid4()),
    }


def test_lists_items_and_returns_item_detail():
    db = ShopSession(build_user(), build_item())

    listing = request(db, "GET", "/items")
    detail = request(db, "GET", "/items/4")

    assert listing.status_code == 200
    assert listing.json()[0]["price"] == 600
    assert detail.status_code == 200
    assert detail.json()["name"] == "학습용 책상"


def test_returns_common_not_found_for_missing_item():
    db = ShopSession(build_user(), None)

    response = request(db, "GET", "/items/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_purchase_uses_current_user_and_server_price():
    user = build_user(soft_balance=1000)
    db = ShopSession(user, build_item())

    response = request(db, "POST", "/shop/buy", purchase_payload())

    assert response.status_code == 200
    assert response.json()["current_soft_balance"] == 400
    assert response.json()["quantity"] == 1
    assert response.json()["replayed"] is False
    assert user.soft_balance == 400
    assert db.added.user_id == user.id
    assert db.committed is True


def test_purchase_increments_existing_inventory_quantity():
    user = build_user(soft_balance=1000)
    item = build_item()
    db = ShopSession(user, item)
    db.inventory = Inventory(
        id=uuid.uuid4(),
        user_id=user.id,
        item_id=item.id,
        quantity=2,
        last_purchase_request_id=uuid.uuid4(),
    )

    response = request(db, "POST", "/shop/buy", purchase_payload())

    assert response.status_code == 200
    assert response.json()["quantity"] == 3
    assert db.inventory.quantity == 3
    assert db.added is None


def test_rejects_body_user_id_and_client_price():
    db = ShopSession(build_user(), build_item())
    payload = purchase_payload()
    payload.update(user_id=str(uuid.uuid4()), price=1)

    response = request(db, "POST", "/shop/buy", payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert db.committed is False


def test_rejects_insufficient_soft_balance_without_inventory_change():
    db = ShopSession(build_user(soft_balance=599), build_item())

    response = request(db, "POST", "/shop/buy", purchase_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_SOFT_BALANCE"
    assert db.added is None
    assert db.committed is False


def test_same_purchase_request_is_replayed_without_second_charge():
    user = build_user(soft_balance=400)
    item = build_item()
    request_id = uuid.uuid4()
    db = ShopSession(user, item)
    db.replayed = Inventory(
        id=uuid.uuid4(),
        user_id=user.id,
        item_id=item.id,
        quantity=2,
        last_purchase_request_id=request_id,
    )

    response = request(
        db,
        "POST",
        "/shop/buy",
        purchase_payload(request_id=request_id),
    )

    assert response.status_code == 200
    assert response.json()["replayed"] is True
    assert response.json()["quantity"] == 2
    assert user.soft_balance == 400
    assert db.committed is False


def test_rejects_request_id_reused_for_different_purchase():
    user = build_user()
    request_id = uuid.uuid4()
    db = ShopSession(user, build_item())
    db.replayed = Inventory(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        item_id=3,
        quantity=1,
        last_purchase_request_id=request_id,
    )

    response = request(
        db,
        "POST",
        "/shop/buy",
        purchase_payload(request_id=request_id),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PURCHASE_REQUEST_CONFLICT"


def test_rolls_back_when_purchase_commit_fails():
    db = ShopSession(build_user(), build_item())
    db.fail_commit = True

    response = request(db, "POST", "/shop/buy", purchase_payload())

    assert response.status_code == 500
    assert db.rolled_back is True


def test_inventory_is_private_to_current_user():
    user = build_user()
    db = ShopSession(user, build_item())
    db.inventory_rows = [(4, "FURNITURE", "학습용 책상", 600, 2)]

    own = request(db, "GET", f"/users/{user.id}/inventory")
    other = request(db, "GET", f"/users/{uuid.uuid4()}/inventory")

    assert own.status_code == 200
    assert own.json()[0]["quantity"] == 2
    assert other.status_code == 403
    assert other.json()["error"]["code"] == "USER_ACCESS_DENIED"
