from sqlalchemy.orm import declarative_base
from smse_backend import db

Base = declarative_base()
Base.metadata = db.metadata
Base.query = db.session.query_property()


class BaseModel(Base):
    __abstract__ = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
