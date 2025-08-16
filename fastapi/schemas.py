from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str
    age: int


class UserCreate(UserBase):
    pass


class UserPost(UserBase):
    id: int
    model_config = ConfigDict(
        from_attributes=True,
    )


class PostBase(BaseModel):
    title: str
    body: str
    author_id: int


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    author: UserPost
    model_config = ConfigDict(
        from_attributes=True,
    )
