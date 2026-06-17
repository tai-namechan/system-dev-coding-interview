import secrets
from datetime import datetime
from typing import List, Optional

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy.orm import Session

from . import models, schemas

pwd_context = PasswordHash([BcryptHasher()])


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.id == user_id, models.User.is_active == True)  # noqa: E712
        .first()
    )


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def get_user_by_api_token(db: Session, api_token: str) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(models.User.api_token == api_token, models.User.is_active == True)  # noqa: E712
        .first()
    )


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = pwd_context.hash(user.password)
    api_token = secrets.token_hex(32)
    db_user = models.User(email=user.email, hashed_password=hashed_password, api_token=api_token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user: models.User) -> None:
    # 有効なユーザーの中で id が最小のユーザーを移管先として選ぶ
    new_owner = (
        db.query(models.User)
        .filter(models.User.is_active == True, models.User.id != user.id)  # noqa: E712
        .order_by(models.User.id.asc())
        .first()
    )

    if new_owner is not None:
        # 削除対象ユーザーの item を一括で新オーナーへ移管する
        db.query(models.Item).filter(models.Item.owner_id == user.id).update(
            {"owner_id": new_owner.id}
        )

    # ユーザーを論理削除する（物理削除はしない）
    user.is_active = False

    # item 移管とユーザー非活性化を同一トランザクションでコミットする
    db.commit()


def get_item(
    db: Session,
    user_id: int,
    item_id: int,
) -> Optional[models.Item]:
    q = db.query(models.Item).filter(
        models.Item.owner_id == user_id, models.Item.id == item_id
    )
    return q.first()


def get_items_by_user(
    db: Session,
    user_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    done: bool | None = None,
) -> List[models.Item]:
    q = db.query(models.Item).filter(models.Item.owner_id == user_id)
    if date_from is not None and date_to is not None:
        q = q.filter(models.Item.created_at >= date_from, models.Item.created_at < date_to)
    if done is not None:
        q = q.filter(models.Item.done == done)
    return q.order_by(models.Item.created_at.desc()).all()


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.Item]:
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(
    db: Session, item: schemas.ItemCreate, user_id: int
) -> models.Item:
    db_item = models.Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_user_item(
    db: Session, item: schemas.ItemUpdate, db_item: models.Item
) -> models.Item:
    if item.title is not None:
        db_item.title = item.title
    if item.description is not None:
        db_item.description = item.description
    if item.done is not None:
        db_item.done = item.done
    db.commit()
    db.refresh(db_item)
    return db_item
