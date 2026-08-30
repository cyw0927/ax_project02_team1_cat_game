import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.housing.models import PlacedObject
from app.main import app
from app.users.models import User


def build_user():
    return User(
        id=uuid.uuid4(),
        external_student_id=f"HOUSE-{uuid.uuid4()}",
        username="하우징 테스트 사용자",
        role="USER",
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


def build_item(category="FURNITURE", item_id=3):
    return Item(id=item_id, category=category, name="테스트 아이템", price=100)


class Result:
    def __init__(self, *, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def one_or_none(self):
        return self.row

    def all(self):
        return self.rows


class HousingSession:
    def __init__(self, user):
        self.user = user
        self.owned_item = build_item()
        self.inventory = Inventory(
            id=uuid.uuid4(),
            user_id=user.id,
            item_id=self.owned_item.id,
            quantity=2,
            last_purchase_request_id=None,
        )
        self.house_rows = []
        self.placed_count = 0
        self.placed_object = None
        self.added = None
        self.deleted = None
        self.committed = False
        self.rolled_back = False
        self.fail_commit = False

    def get(self, model, identity, **kwargs):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def execute(self, statement):
        statement_text = str(statement)
        if "FROM items JOIN inventories" in statement_text:
            row = None
            if self.owned_item is not None:
                row = (self.owned_item, self.inventory)
            return Result(row=row)
        return Result(rows=self.house_rows)

    def scalar(self, statement):
        statement_text = str(statement)
        if "count(placed_objects.id)" in statement_text:
            return self.placed_count
        return self.placed_object

    def add(self, placed_object):
        self.added = placed_object
        self.placed_object = placed_object

    def delete(self, placed_object):
        self.deleted = placed_object

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True
        if self.added is not None and self.added.id is None:
            self.added.id = uuid.uuid4()

    def rollback(self):
        self.rolled_back = True

    def refresh(self, row):
        pass


def request(db, method, path, json=None, *, current_user=True):
    def override_get_db():
        yield db

    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        headers = {"X-User-ID": str(db.user.id)} if current_user else {}
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, headers=headers, json=json)

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(send())
    finally:
        app.dependency_overrides.clear()


def position(**changes):
    value = {"x": 25, "y": 60, "rotation": 0, "scale": 1}
    value.update(changes)
    return value


def test_house_is_publicly_readable_for_another_user():
    user = build_user()
    db = HousingSession(user)
    placed_id = uuid.uuid4()
    db.house_rows = [
        (placed_id, 3, "FURNITURE", "기본 캣타워", position())
    ]

    response = request(
        db,
        "GET",
        f"/users/{user.id}/house",
        current_user=False,
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == str(user.id)
    assert response.json()["placed_objects"][0]["placed_object_id"] == str(placed_id)


def test_places_owned_furniture_and_normalizes_position():
    user = build_user()
    db = HousingSession(user)

    response = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": {"x": 20, "y": 70}},
    )

    assert response.status_code == 201
    assert db.added.position_data == {
        "x": 20.0,
        "y": 70.0,
        "rotation": 0.0,
        "scale": 1.0,
    }
    assert db.committed is True


def test_rejects_invalid_or_unknown_position_fields():
    user = build_user()
    db = HousingSession(user)

    out_of_bounds = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": position(x=101)},
    )
    unknown = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": {**position(), "script": "bad"}},
    )

    assert out_of_bounds.status_code == 422
    assert unknown.status_code == 422
    assert db.added is None


def test_rejects_unowned_and_non_furniture_items():
    user = build_user()
    db = HousingSession(user)
    db.owned_item = None
    unowned = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": position()},
    )

    db.owned_item = build_item("WALLPAPER", 1)
    db.inventory.item_id = 1
    surface = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 1, "position_data": position()},
    )

    assert unowned.status_code == 409
    assert unowned.json()["error"]["code"] == "ITEM_NOT_OWNED"
    assert surface.status_code == 409
    assert surface.json()["error"]["code"] == "ITEM_NOT_PLACEABLE"


def test_rejects_placement_over_owned_quantity():
    user = build_user()
    db = HousingSession(user)
    db.inventory.quantity = 2
    db.placed_count = 2

    response = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": position()},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PLACEMENT_QUANTITY_EXCEEDED"


def test_other_user_cannot_mutate_house():
    user = build_user()
    db = HousingSession(user)

    response = request(
        db,
        "POST",
        f"/users/{uuid.uuid4()}/house/objects",
        {"item_id": 3, "position_data": position()},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_ACCESS_DENIED"
    assert db.added is None


def test_moves_and_removes_owned_placed_object():
    user = build_user()
    db = HousingSession(user)
    placed = PlacedObject(
        id=uuid.uuid4(),
        user_id=user.id,
        item_id=3,
        position_data=position(),
    )
    db.placed_object = placed

    moved = request(
        db,
        "PATCH",
        f"/users/{user.id}/house/objects/{placed.id}",
        {"position_data": position(x=40)},
    )
    removed = request(
        db,
        "DELETE",
        f"/users/{user.id}/house/objects/{placed.id}",
    )

    assert moved.status_code == 200
    assert moved.json()["position_data"]["x"] == 40
    assert removed.status_code == 200
    assert db.deleted is placed


def test_applies_only_matching_surface_categories():
    user = build_user()
    db = HousingSession(user)
    db.owned_item = build_item("WALLPAPER", 1)
    db.inventory.item_id = 1

    wallpaper = request(
        db,
        "PUT",
        f"/users/{user.id}/house/wallpaper",
        {"item_id": 1},
    )
    invalid_floor = request(
        db,
        "PUT",
        f"/users/{user.id}/house/floor",
        {"item_id": 1},
    )

    assert wallpaper.status_code == 200
    assert wallpaper.json() == {"surface": "WALLPAPER", "item_id": 1}
    assert user.wallpaper_item_id == 1
    assert invalid_floor.status_code == 409
    assert invalid_floor.json()["error"]["code"] == "INVALID_SURFACE_CATEGORY"


def test_rolls_back_when_placement_commit_fails():
    user = build_user()
    db = HousingSession(user)
    db.fail_commit = True

    response = request(
        db,
        "POST",
        f"/users/{user.id}/house/objects",
        {"item_id": 3, "position_data": position()},
    )

    assert response.status_code == 500
    assert db.rolled_back is True
