import asyncio
import uuid
from datetime import UTC, datetime

import httpx

import app.gacha.router as gacha_router
from app.cats.models import Cat, UserCat
from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.gacha.policy import (
    REGULAR_POOL,
    TEN_PULL_GUARANTEED_POOL,
    choose_prize,
)
from app.main import app
from app.users.models import User


def build_user(*, hard_balance=100, mileage=0):
    return User(
        id=uuid.uuid4(),
        external_student_id=f"GACHA-{uuid.uuid4()}",
        username="가챠 테스트 사용자",
        role="USER",
        soft_balance=0,
        hard_balance=hard_balance,
        mileage=mileage,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


class Scalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class GachaSession:
    def __init__(self, user):
        self.user = user
        self.cats = {
            1: Cat(id=1, name="나비", persona="p", rarity="N"),
            2: Cat(id=2, name="구름", persona="p", rarity="R"),
            3: Cat(id=3, name="별이", persona="p", rarity="SR"),
            4: Cat(id=4, name="루나", persona="p", rarity="SSR"),
        }
        self.items = {
            item_id: Item(
                id=item_id,
                category="FURNITURE",
                name=name,
                price=100,
            )
            for item_id, name in (
                (1, "파란 별 벽지"),
                (2, "원목 바닥"),
                (3, "기본 캣타워"),
                (4, "학습용 책상"),
            )
        }
        self.owned_cat_ids = set()
        self.inventories = {}
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.fail_commit = False

    def get(self, model, identity, **kwargs):
        if model is User and identity == self.user.id:
            return self.user
        if model is Cat:
            return self.cats.get(identity)
        if model is Item:
            return self.items.get(identity)
        return None

    def scalars(self, statement):
        statement_text = str(statement)
        if "user_cats.cat_id" in statement_text:
            return Scalars(list(self.owned_cat_ids))
        if "FROM inventories" in statement_text:
            return Scalars(list(self.inventories.values()))
        return Scalars([])

    def add(self, row):
        self.added.append(row)
        if isinstance(row, Inventory):
            self.inventories[row.item_id] = row

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


def pull_payload(count=1, request_id=None, **extra):
    return {
        "count": count,
        "request_id": str(request_id or uuid.uuid4()),
        **extra,
    }


def test_gacha_info_exposes_server_costs_probabilities_and_guarantee():
    response = request(GachaSession(build_user()), "GET", "/gacha")

    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "HARD"
    assert body["single_cost"] == 10
    assert body["ten_cost"] == 90
    assert sum(entry["probability_percent"] for entry in body["pool"]) == 100
    assert "SR" in body["ten_pull_guarantee"]


def test_weighted_selection_uses_exact_boundaries():
    assert choose_prize(REGULAR_POOL, lambda _: 0).target_id == 1
    assert choose_prize(REGULAR_POOL, lambda _: 39).target_id == 1
    assert choose_prize(REGULAR_POOL, lambda _: 40).target_id == 2
    assert choose_prize(REGULAR_POOL, lambda _: 99).target_id == 4
    assert choose_prize(REGULAR_POOL, lambda _: 99).reward_type == "ITEM"


def test_single_pull_grants_new_cat_and_deducts_hard_balance(monkeypatch):
    db = GachaSession(build_user())
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[1])

    response = request(db, "POST", "/gacha/pull", pull_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["current_hard_balance"] == 90
    assert body["results"][0]["is_new"] is True
    assert any(isinstance(row, UserCat) and row.cat_id == 2 for row in db.added)
    assert db.committed is True


def test_duplicate_cat_is_converted_to_rarity_mileage(monkeypatch):
    db = GachaSession(build_user(mileage=3))
    db.owned_cat_ids.add(2)
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[1])

    response = request(db, "POST", "/gacha/pull", pull_payload())

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["is_new"] is False
    assert result["mileage_awarded"] == 10
    assert response.json()["current_mileage"] == 13
    assert not any(isinstance(row, UserCat) for row in db.added)


def test_item_reward_increments_inventory(monkeypatch):
    db = GachaSession(build_user())
    db.inventories[4] = Inventory(
        id=uuid.uuid4(),
        user_id=db.user.id,
        item_id=4,
        quantity=2,
        last_purchase_request_id=None,
    )
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[-1])

    response = request(db, "POST", "/gacha/pull", pull_payload())

    result = response.json()["results"][0]
    assert result["reward_type"] == "ITEM"
    assert result["quantity"] == 3
    assert result["is_new"] is False
    assert db.inventories[4].quantity == 3


def test_ten_pull_charges_discount_and_guarantees_last_sr_cat(monkeypatch):
    db = GachaSession(build_user())

    def pick(pool):
        if pool is TEN_PULL_GUARANTEED_POOL:
            return TEN_PULL_GUARANTEED_POOL[0]
        return REGULAR_POOL[-1]

    monkeypatch.setattr(gacha_router, "choose_prize", pick)
    response = request(db, "POST", "/gacha/pull", pull_payload(10))

    body = response.json()
    assert response.status_code == 200
    assert body["cost"] == 90
    assert body["current_hard_balance"] == 10
    assert len(body["results"]) == 10
    assert body["results"][-1]["rarity"] == "SR"
    assert body["results"][-1]["reward_type"] == "CAT"
    assert db.inventories[4].quantity == 9


def test_repeated_cat_in_same_pull_becomes_duplicate_after_first(monkeypatch):
    db = GachaSession(build_user())

    def pick(pool):
        if pool is TEN_PULL_GUARANTEED_POOL:
            return TEN_PULL_GUARANTEED_POOL[0]
        return REGULAR_POOL[1]

    monkeypatch.setattr(gacha_router, "choose_prize", pick)
    response = request(db, "POST", "/gacha/pull", pull_payload(10))

    assert response.status_code == 200
    assert response.json()["current_mileage"] == 80
    cat_twos = [row for row in db.added if isinstance(row, UserCat) and row.cat_id == 2]
    assert len(cat_twos) == 1


def test_insufficient_balance_and_invalid_body_do_not_mutate(monkeypatch):
    db = GachaSession(build_user(hard_balance=9))
    called = False

    def pick(pool):
        nonlocal called
        called = True
        return REGULAR_POOL[0]

    monkeypatch.setattr(gacha_router, "choose_prize", pick)
    insufficient = request(db, "POST", "/gacha/pull", pull_payload())
    invalid = request(db, "POST", "/gacha/pull", pull_payload(2, price=0))

    assert insufficient.status_code == 409
    assert insufficient.json()["error"]["code"] == "INSUFFICIENT_HARD_BALANCE"
    assert invalid.status_code == 422
    assert called is False
    assert db.committed is False


def test_commit_failure_rolls_back_whole_pull(monkeypatch):
    db = GachaSession(build_user())
    db.fail_commit = True
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[0])

    response = request(db, "POST", "/gacha/pull", pull_payload())

    assert response.status_code == 500
    assert db.rolled_back is True


def test_same_request_is_replayed_and_result_can_be_queried(monkeypatch):
    db = GachaSession(build_user())
    request_id = uuid.uuid4()
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[1])

    first = request(db, "POST", "/gacha/pull", pull_payload(request_id=request_id))
    balance_after_first = db.user.hard_balance
    replay = request(db, "POST", "/gacha/pull", pull_payload(request_id=request_id))
    result = request(db, "GET", f"/gacha/results/{request_id}")

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert result.status_code == 200
    assert db.user.hard_balance == balance_after_first
    assert len([row for row in db.added if isinstance(row, UserCat)]) == 1


def test_request_id_cannot_be_reused_for_different_count(monkeypatch):
    db = GachaSession(build_user())
    request_id = uuid.uuid4()
    monkeypatch.setattr(gacha_router, "choose_prize", lambda pool: REGULAR_POOL[1])
    request(db, "POST", "/gacha/pull", pull_payload(request_id=request_id))

    conflict = request(
        db,
        "POST",
        "/gacha/pull",
        pull_payload(10, request_id=request_id),
    )

    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "GACHA_REQUEST_CONFLICT"
