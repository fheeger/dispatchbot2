import httpx
from pydantic import TypeAdapter

from client.errors import BackendError
from client.models import (
    AccountCreatedResponse,
    AddCategoryResponse,
    CategoryResponse,
    ChannelResponse,
    ChannelsRemovedResponse,
    ChannelsUpdatedResponse,
    GameCreatedResponse,
    GameEndedResponse,
    Message,
    RemoveCategoryResponse,
    RoundResponse,
    TurnAdvancedResponse,
)


class BackendClient:
    def __init__(self, base_url: str):
        self._http = httpx.AsyncClient(base_url=base_url)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str, *,
                       params: dict | None = None,
                       json: dict | None = None) -> dict | list:
        response = await self._http.request(method, path, params=params, json=json)
        if response.is_error:
            body = response.json()
            raise BackendError(response.status_code, body["error_type"], body["message"])
        return response.json()

    def _game_params(self, server_id: int, category_id: int) -> dict:
        return {"server_id": server_id, "category_id": category_id}

    # --- Account ---

    async def create_user(self, username: str, discord_id_hash: str) -> AccountCreatedResponse:
        data = await self._request("POST", "bot/new_user/", json={
            "username": username,
            "discord_user_id_hash": discord_id_hash,
        })
        return AccountCreatedResponse.model_validate(data)

    # --- Game lifecycle ---

    async def create_game(self, name: str, server_id: int, discord_id_hash: str) -> GameCreatedResponse:
        data = await self._request("POST", "bot/new_game/", json={
            "name_game": name,
            "server_id": server_id,
            "discord_user_id_hash": discord_id_hash,
            "user_id": 0,
            "channels": [],
        })
        return GameCreatedResponse.model_validate(data)

    async def get_round(self, server_id: int, category_id: int) -> RoundResponse:
        data = await self._request("GET", "bot/get_round/",
                                   params=self._game_params(server_id, category_id))
        return RoundResponse.model_validate(data)

    async def next_turn(self, server_id: int, category_id: int) -> TurnAdvancedResponse:
        data = await self._request("POST", "bot/next_turn/",
                                   params=self._game_params(server_id, category_id))
        return TurnAdvancedResponse.model_validate(data)

    async def end_game(self, server_id: int, category_id: int) -> GameEndedResponse:
        data = await self._request("POST", "bot/end_game/",
                                   params=self._game_params(server_id, category_id))
        return GameEndedResponse.model_validate(data)

    # --- Messages ---

    async def get_messages(self, server_id: int, category_id: int) -> list[Message]:
        data = await self._request("GET", "bot/get_messages/",
                                   params=self._game_params(server_id, category_id))
        return TypeAdapter(list[Message]).validate_python(data)

    async def check_unapproved_messages(self, server_id: int, category_id: int) -> list[Message]:
        data = await self._request("GET", "bot/check_messages/",
                                   params=self._game_params(server_id, category_id))
        return TypeAdapter(list[Message]).validate_python(data)

    async def send_message(self, server_id: int, category_id: int,
                           text: str, sender: str) -> Message:
        data = await self._request("POST", "bot/send_message/",
                                   params=self._game_params(server_id, category_id),
                                   json={"text": text, "sender": sender})
        return Message.model_validate(data)

    # --- Categories ---

    async def add_categories(self, game_name: str, server_id: int,
                             category_ids: list[int]) -> AddCategoryResponse:
        data = await self._request("POST", f"bot/add_category/{game_name}/",
                                   params={"server_id": server_id},
                                   json={"category": category_ids})
        return AddCategoryResponse.model_validate(data)

    async def remove_categories(self, game_name: str, server_id: int,
                                category_ids: list[int]) -> RemoveCategoryResponse:
        data = await self._request("POST", f"bot/remove_category/{game_name}/",
                                   params={"server_id": server_id},
                                   json={"category": category_ids})
        return RemoveCategoryResponse.model_validate(data)

    async def list_categories(self, game_name: str, server_id: int) -> list[CategoryResponse]:
        data = await self._request("GET", f"bot/get_categories/{game_name}/",
                                   params={"server_id": server_id})
        return TypeAdapter(list[CategoryResponse]).validate_python(data)

    # --- Channels ---

    async def update_channels(self, server_id: int, category_id: int,
                              channels: dict[int, str]) -> ChannelsUpdatedResponse:
        data = await self._request("POST", "bot/update_channels/",
                                   params=self._game_params(server_id, category_id),
                                   json={"channels": {str(k): v for k, v in channels.items()}})
        return ChannelsUpdatedResponse.model_validate(data)

    async def remove_channels(self, server_id: int, category_id: int,
                              channels: dict[int, str]) -> ChannelsRemovedResponse:
        data = await self._request("POST", "bot/remove_channels/",
                                   params=self._game_params(server_id, category_id),
                                   json={"channels": [str(k) for k in channels]})
        return ChannelsRemovedResponse.model_validate(data)

    async def list_channels(self, server_id: int, category_id: int) -> list[ChannelResponse]:
        data = await self._request("GET", "bot/get_channels/",
                                   params=self._game_params(server_id, category_id))
        return TypeAdapter(list[ChannelResponse]).validate_python(data)
