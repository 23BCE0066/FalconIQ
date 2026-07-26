"""
Base Class: BaseRepository

Generic typed repository. Concrete implementations inject a SQLModel session
and override CRUD methods. Never contains business logic — only data access.

Generic Type Parameter:
    ModelType: The SQLModel table class this repository manages.
    CreateType: The Pydantic schema used to create a new record.
"""
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlmodel import SQLModel, Session, select

from app.core.exceptions import RepositoryException

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateType = TypeVar("CreateType", bound=SQLModel)


class BaseRepository(ABC, Generic[ModelType, CreateType]):
    """
    Abstract generic repository.

    Concrete subclasses must set `model` to their SQLModel table class.
    The session is injected at construction time (Dependency Injection).
    """

    model: Type[ModelType]

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, id: Any) -> Optional[ModelType]:
        """Retrieves a single entity by primary key. Returns None if not found."""
        try:
            return self._session.get(self.model, id)
        except Exception as exc:
            raise RepositoryException(f"Failed to fetch {self.model.__name__} by id '{id}': {exc}") from exc

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieves a paginated list of entities."""
        try:
            statement = select(self.model).offset(skip).limit(limit)
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(f"Failed to list {self.model.__name__}: {exc}") from exc

    def create(self, *, obj_in: CreateType) -> ModelType:
        """Creates and persists a new entity from the given schema."""
        try:
            db_obj = self.model.model_validate(obj_in.model_dump())
            self._session.add(db_obj)
            self._session.commit()
            self._session.refresh(db_obj)
            return db_obj
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(f"Failed to create {self.model.__name__}: {exc}") from exc

    def update(self, *, db_obj: ModelType, updates: dict) -> ModelType:
        """Applies a partial update dict to an existing entity."""
        try:
            for key, value in updates.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self._session.add(db_obj)
            self._session.commit()
            self._session.refresh(db_obj)
            return db_obj
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(f"Failed to update {self.model.__name__}: {exc}") from exc

    def remove(self, *, id: Any) -> Optional[ModelType]:
        """Deletes an entity by primary key. Returns the deleted object."""
        try:
            obj = self.get(id)
            if obj:
                self._session.delete(obj)
                self._session.commit()
            return obj
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(f"Failed to delete {self.model.__name__} '{id}': {exc}") from exc
