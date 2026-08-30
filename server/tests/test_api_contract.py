from app.battle.models import RoomParticipant, RoomTask
from app.main import app
from app.ranking.models import RankChallengeTask, RankingParticipant


def test_new_write_routes_are_registered():
    paths = app.openapi()["paths"]
    routes = {
        (path, method.upper())
        for path, operations in paths.items()
        for method in operations
    }

    assert ("/users/{user_id}/house/objects", "POST") in routes
    assert ("/users/{user_id}/house/objects/{placed_object_id}", "PATCH") in routes
    assert ("/users/{user_id}/house/objects/{placed_object_id}", "DELETE") in routes
    assert ("/users/{user_id}/house/wallpaper", "PUT") in routes
    assert ("/users/{user_id}/house/floor", "PUT") in routes
    assert ("/users/{user_id}/cats/starter", "POST") in routes
    assert ("/ranking-groups/{group_id}/rank-challenges", "POST") in routes
    assert ("/rank-challenges/{challenge_id}/tasks/{task_id}/code", "PUT") in routes


def test_concurrency_sensitive_tables_have_database_constraints():
    constraint_names = {
        constraint.name
        for table in (
            RoomParticipant.__table__,
            RoomTask.__table__,
            RankingParticipant.__table__,
            RankChallengeTask.__table__,
        )
        for constraint in table.constraints
        if constraint.name
    }

    assert "uq_room_participants_room_user" in constraint_names
    assert "uq_room_tasks_room_task" in constraint_names
    assert "uq_room_tasks_room_order" in constraint_names
    assert "uq_ranking_participants_group_user" in constraint_names
    assert "uq_rank_challenge_tasks_challenge_task" in constraint_names
    assert "uq_rank_challenge_tasks_challenge_order" in constraint_names
