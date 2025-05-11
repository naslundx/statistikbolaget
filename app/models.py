import uuid
from pydantic import BaseModel


class UserQuery(BaseModel):
    question: str


class VoteQuery(BaseModel):
    uuid: uuid.UUID
    upvote: bool
