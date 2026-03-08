from pydantic import BaseModel, Field


class AccountCreatedResponse(BaseModel):
    username: str
    is_staff: bool
    password: str


class GameCreatedResponse(BaseModel):
    name: str
    turn: int
    start_time: str | None
    server_id: int | None
    user_id: int | None


class RoundResponse(BaseModel):
    # All fields are nullable: the backend returns nulls when no game is currently running.
    turn: int | None
    name: str | None
    start_time: str | None
    server_id: int | None
    user_id: int | None


class TurnAdvancedResponse(BaseModel):
    name: str
    turn: int
    current_time: str


class GameEndedResponse(BaseModel):
    name: str
    turn: int
    current_time: str


class RecipientChannel(BaseModel):
    channel_id: int = Field(alias="channelId")
    channel_name: str = Field(alias="channelName")

    model_config = {"populate_by_name": True}


class Message(BaseModel):
    text: str
    sender: str
    show_sender: bool = Field(alias="showSender")
    channels_list: list[RecipientChannel]
    turn_when_sent: int
    turn_when_received: int | None
    game: int

    model_config = {"populate_by_name": True}


class AddCategoryResponse(BaseModel):
    game: str
    categories: list[int]  # plural — matches the backend's response key


class RemoveCategoryResponse(BaseModel):
    game: str
    category: list[int]  # singular — intentional asymmetry with AddCategoryResponse, mirrors the backend API


class CategoryResponse(BaseModel):
    number: int
    game: int


class ChannelResponse(BaseModel):
    channel_id: int
    name: str
    game: int


class ChannelsUpdatedResponse(BaseModel):
    game: str
    channels: dict[str, str]


class ChannelsRemovedResponse(BaseModel):
    game: str
    channels: list[str]
