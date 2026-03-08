import httpx
import pytest
import respx

from client.backend_client import BackendClient
from client.errors import BackendError

BASE_URL = "http://testserver/"
MOCK_ERROR = {"error_type": "Game Not Found", "message": "No game found"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def error_response(error_type: str, message: str, status: int) -> httpx.Response:
    return httpx.Response(status, json={"error_type": error_type, "message": message})


# ---------------------------------------------------------------------------
# POST /bot/new_user/
# ---------------------------------------------------------------------------

class TestCreateUser:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, discord_id_hash):
        respx.post(f"{BASE_URL}bot/new_user/").mock(return_value=httpx.Response(201, json={
            "username": "john",
            "is_staff": False,
            "password": "abc1234xyz",
        }))

        result = await client.create_user("john", discord_id_hash)

        assert result.username == "john"
        assert result.is_staff is False
        assert result.password == "abc1234xyz"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_body(self, client, discord_id_hash):
        import json
        route = respx.post(f"{BASE_URL}bot/new_user/").mock(return_value=httpx.Response(201, json={
            "username": "john", "is_staff": False, "password": "abc1234xyz",
        }))

        await client.create_user("john", discord_id_hash)

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"username": "john", "discord_user_id_hash": discord_id_hash}

    @respx.mock
    @pytest.mark.asyncio
    async def test_user_already_exists(self, client, discord_id_hash):
        respx.post(f"{BASE_URL}bot/new_user/").mock(return_value=error_response(
            "User Already Exists", "An user with the username john already exists", 400
        ))

        with pytest.raises(BackendError) as exc:
            await client.create_user("john", discord_id_hash)

        assert exc.value.error_type == "User Already Exists"
        assert exc.value.status == 400


# ---------------------------------------------------------------------------
# POST /bot/new_game/
# ---------------------------------------------------------------------------

class TestCreateGame:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, discord_id_hash):
        respx.post(f"{BASE_URL}bot/new_game/").mock(return_value=httpx.Response(201, json={
            "name": "Test-Game",
            "turn": 1,
            "start_time": "08:00:00",
            "server_id": server_id,
            "user_id": None,
        }))

        result = await client.create_game("Test-Game", server_id, discord_id_hash)

        assert result.name == "Test-Game"
        assert result.turn == 1
        assert result.start_time == "08:00:00"
        assert result.server_id == server_id

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_account(self, client, server_id, discord_id_hash):
        respx.post(f"{BASE_URL}bot/new_game/").mock(return_value=error_response(
            "No Account", "You don't have an account", 403
        ))

        with pytest.raises(BackendError) as exc:
            await client.create_game("Test-Game", server_id, discord_id_hash)

        assert exc.value.error_type == "No Account"
        assert exc.value.status == 403

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_already_exists(self, client, server_id, discord_id_hash):
        respx.post(f"{BASE_URL}bot/new_game/").mock(return_value=error_response(
            "Game Already Exists", "A game with the same name is already going on!", 422
        ))

        with pytest.raises(BackendError) as exc:
            await client.create_game("Test-Game", server_id, discord_id_hash)

        assert exc.value.error_type == "Game Already Exists"
        assert exc.value.status == 422


# ---------------------------------------------------------------------------
# GET /bot/get_round/
# ---------------------------------------------------------------------------

class TestGetRound:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_round/").mock(return_value=httpx.Response(200, json={
            "turn": 3,
            "name": "Test-Game",
            "start_time": "08:00:00",
            "server_id": server_id,
            "user_id": None,
        }))

        result = await client.get_round(server_id, category_id)

        assert result.turn == 3
        assert result.name == "Test-Game"

    @respx.mock
    @pytest.mark.asyncio
    async def test_turn_is_null_when_no_game(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_round/").mock(return_value=httpx.Response(200, json={
            "turn": None, "name": None, "start_time": None,
            "server_id": None, "user_id": None,
        }))

        result = await client.get_round(server_id, category_id)

        assert result.turn is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_round/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.get_round(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"
        assert exc.value.status == 404

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_ambiguous(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_round/").mock(return_value=error_response(
            "Game Ambiguous", "Can not decide which game you want", 400
        ))

        with pytest.raises(BackendError) as exc:
            await client.get_round(server_id, category_id)

        assert exc.value.error_type == "Game Ambiguous"


# ---------------------------------------------------------------------------
# POST /bot/next_turn/
# ---------------------------------------------------------------------------

class TestNextTurn:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/next_turn/").mock(return_value=httpx.Response(200, json={
            "name": "Test-Game",
            "turn": 4,
            "current_time": "09:00:00",
        }))

        result = await client.next_turn(server_id, category_id)

        assert result.turn == 4
        assert result.current_time == "09:00:00"
        assert result.name == "Test-Game"

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/next_turn/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.next_turn(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/end_game/
# ---------------------------------------------------------------------------

class TestEndGame:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/end_game/").mock(return_value=httpx.Response(200, json={
            "name": "Test-Game",
            "turn": 5,
            "current_time": "12:00:00",
        }))

        result = await client.end_game(server_id, category_id)

        assert result.name == "Test-Game"
        assert result.turn == 5
        assert result.current_time == "12:00:00"

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/end_game/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.end_game(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# GET /bot/get_messages/
# ---------------------------------------------------------------------------

class TestGetMessages:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id, message_payload):
        respx.get(f"{BASE_URL}bot/get_messages/").mock(
            return_value=httpx.Response(200, json=[message_payload])
        )

        result = await client.get_messages(server_id, category_id)

        assert len(result) == 1
        assert result[0].text == message_payload["text"]
        assert result[0].sender == message_payload["sender"]
        assert result[0].show_sender is True
        assert result[0].channels_list[0].channel_id == 333333333333333333
        assert result[0].channels_list[0].channel_name == "alpha-company"
        assert result[0].turn_when_sent == 3
        assert result[0].turn_when_received == 4
        assert result[0].game == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_list(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_messages/").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await client.get_messages(server_id, category_id)

        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_messages/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.get_messages(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# GET /bot/check_messages/
# ---------------------------------------------------------------------------

class TestCheckMessages:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_unapproved_messages(self, client, server_id, category_id, message_payload):
        respx.get(f"{BASE_URL}bot/check_messages/").mock(
            return_value=httpx.Response(200, json=[message_payload, message_payload])
        )

        result = await client.check_unapproved_messages(server_id, category_id)

        assert len(result) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_when_all_approved(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/check_messages/").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await client.check_unapproved_messages(server_id, category_id)

        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/check_messages/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.check_unapproved_messages(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/send_message/
# ---------------------------------------------------------------------------

class TestSendMessage:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id, message_payload):
        respx.post(f"{BASE_URL}bot/send_message/").mock(
            return_value=httpx.Response(201, json=message_payload)
        )

        result = await client.send_message(
            server_id, category_id,
            text="Requesting reinforcements at grid 447.",
            sender="Alpha Company",
        )

        assert result.text == message_payload["text"]
        assert result.sender == message_payload["sender"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_body(self, client, server_id, category_id, message_payload):
        route = respx.post(f"{BASE_URL}bot/send_message/").mock(
            return_value=httpx.Response(201, json=message_payload)
        )

        await client.send_message(server_id, category_id, text="Hello", sender="Alpha")

        import json
        body = json.loads(route.calls.last.request.content)
        assert body["text"] == "Hello"
        assert body["sender"] == "Alpha"

    @respx.mock
    @pytest.mark.asyncio
    async def test_message_too_long(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/send_message/").mock(return_value=error_response(
            "Message Too Long",
            "Your message was too long. The maximum length for messages in this game is 500.",
            422,
        ))

        with pytest.raises(BackendError) as exc:
            await client.send_message(server_id, category_id, text="x" * 1000, sender="Alpha")

        assert exc.value.error_type == "Message Too Long"
        assert exc.value.status == 422

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/send_message/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.send_message(server_id, category_id, text="Hello", sender="Alpha")

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/add_category/<game_name>/
# ---------------------------------------------------------------------------

class TestAddCategory:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, game_name, server_id):
        category_ids = [444444444444444444, 555555555555555555]
        respx.post(f"{BASE_URL}bot/add_category/{game_name}/").mock(
            return_value=httpx.Response(200, json={
                "game": game_name,
                "categories": category_ids,
            })
        )

        result = await client.add_categories(game_name, server_id, category_ids)

        assert result.game == game_name
        assert result.categories == category_ids

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_body(self, client, game_name, server_id):
        category_ids = [444444444444444444]
        route = respx.post(f"{BASE_URL}bot/add_category/{game_name}/").mock(
            return_value=httpx.Response(200, json={"game": game_name, "categories": category_ids})
        )

        await client.add_categories(game_name, server_id, category_ids)

        import json
        body = json.loads(route.calls.last.request.content)
        assert body["category"] == category_ids

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, game_name, server_id):
        respx.post(f"{BASE_URL}bot/add_category/{game_name}/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.add_categories(game_name, server_id, [444444444444444444])

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/remove_category/<game_name>/
# ---------------------------------------------------------------------------

class TestRemoveCategory:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, game_name, server_id):
        remaining = [555555555555555555]
        respx.post(f"{BASE_URL}bot/remove_category/{game_name}/").mock(
            return_value=httpx.Response(200, json={
                "game": game_name,
                "category": remaining,
            })
        )

        result = await client.remove_categories(game_name, server_id, [444444444444444444])

        assert result.game == game_name
        assert result.category == remaining

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, game_name, server_id):
        respx.post(f"{BASE_URL}bot/remove_category/{game_name}/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.remove_categories(game_name, server_id, [444444444444444444])

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# GET /bot/get_categories/<game_name>/
# ---------------------------------------------------------------------------

class TestGetCategories:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, game_name, server_id):
        respx.get(f"{BASE_URL}bot/get_categories/{game_name}/").mock(
            return_value=httpx.Response(200, json=[
                {"number": 444444444444444444, "game": 1},
                {"number": 555555555555555555, "game": 1},
            ])
        )

        result = await client.list_categories(game_name, server_id)

        assert len(result) == 2
        assert result[0].number == 444444444444444444
        assert result[0].game == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty(self, client, game_name, server_id):
        respx.get(f"{BASE_URL}bot/get_categories/{game_name}/").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await client.list_categories(game_name, server_id)

        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, game_name, server_id):
        respx.get(f"{BASE_URL}bot/get_categories/{game_name}/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.list_categories(game_name, server_id)

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/update_channels/
# ---------------------------------------------------------------------------

class TestUpdateChannels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        channels = {333333333333333333: "alpha-company", 444444444444444444: "bravo-company"}
        respx.post(f"{BASE_URL}bot/update_channels/").mock(
            return_value=httpx.Response(200, json={
                "game": "Test-Game",
                "channels": {"333333333333333333": "alpha-company", "444444444444444444": "bravo-company"},
            })
        )

        result = await client.update_channels(server_id, category_id, channels)

        assert result.game == "Test-Game"
        assert result.channels["333333333333333333"] == "alpha-company"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_channel_ids_as_string_keys(self, client, server_id, category_id):
        route = respx.post(f"{BASE_URL}bot/update_channels/").mock(
            return_value=httpx.Response(200, json={"game": "Test-Game", "channels": {}})
        )

        await client.update_channels(server_id, category_id, {123456789: "alpha-company"})

        import json
        body = json.loads(route.calls.last.request.content)
        assert "123456789" in body["channels"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/update_channels/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.update_channels(server_id, category_id, {})

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# POST /bot/remove_channels/
# ---------------------------------------------------------------------------

class TestRemoveChannels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/remove_channels/").mock(
            return_value=httpx.Response(200, json={
                "game": "Test-Game",
                "channels": ["333333333333333333"],
            })
        )

        result = await client.remove_channels(server_id, category_id, {333333333333333333: "alpha-company"})

        assert result.game == "Test-Game"
        assert "333333333333333333" in result.channels

    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_channel_ids_as_string_list(self, client, server_id, category_id):
        route = respx.post(f"{BASE_URL}bot/remove_channels/").mock(
            return_value=httpx.Response(200, json={"game": "Test-Game", "channels": []})
        )

        await client.remove_channels(server_id, category_id, {123456789: "alpha-company"})

        import json
        body = json.loads(route.calls.last.request.content)
        assert body["channels"] == ["123456789"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.post(f"{BASE_URL}bot/remove_channels/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.remove_channels(server_id, category_id, {})

        assert exc.value.error_type == "Game Not Found"


# ---------------------------------------------------------------------------
# GET /bot/get_channels/
# ---------------------------------------------------------------------------

class TestGetChannels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_channels/").mock(
            return_value=httpx.Response(200, json=[
                {"channel_id": 333333333333333333, "name": "alpha-company", "game": 1},
                {"channel_id": 444444444444444444, "name": "bravo-company", "game": 1},
            ])
        )

        result = await client.list_channels(server_id, category_id)

        assert len(result) == 2
        assert result[0].channel_id == 333333333333333333
        assert result[0].name == "alpha-company"
        assert result[0].game == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_channels/").mock(
            return_value=httpx.Response(200, json=[])
        )

        result = await client.list_channels(server_id, category_id)

        assert result == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_not_found(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_channels/").mock(return_value=error_response(
            "Game Not Found", "No game found", 404
        ))

        with pytest.raises(BackendError) as exc:
            await client.list_channels(server_id, category_id)

        assert exc.value.error_type == "Game Not Found"

    @respx.mock
    @pytest.mark.asyncio
    async def test_game_ambiguous(self, client, server_id, category_id):
        respx.get(f"{BASE_URL}bot/get_channels/").mock(return_value=error_response(
            "Game Ambiguous", "Can not decide which game you want", 400
        ))

        with pytest.raises(BackendError) as exc:
            await client.list_channels(server_id, category_id)

        assert exc.value.error_type == "Game Ambiguous"
