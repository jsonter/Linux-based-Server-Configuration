import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):

    __tablename__ = 'User'

    id = Column(Integer, primary_key = True)
    name = Column(String(30), nullable = False)
    email = Column(String(100), unique = True)
    picture = Column(String(100))

class Category(Base):

    __tablename__ = 'Category'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship(User)
    items = relationship('Item', cascade = 'delete')

    @property
    def serialize(self):

        return {
            'id': self.id,
            'name': self.name
        }

class Item(Base):

    __tablename__ = 'Item'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('Category.id'))
    user_id = Column(Integer, ForeignKey('User.id'))
    picture = Column(String(100))
    category = relationship(Category)
    user = relationship(User)

    @property
    def serialize(self):

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'picture': self.picture
        }


engine = create_engine('postgresql://catalog:fgRT56rkG@localhost/catalog')

Base.metadata.create_all(engine)
