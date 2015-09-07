from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Category, Base, Item

engine = create_engine('postgresql://catalog:fgRT56rkG@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Add a user
user1 = User(name = "Justin Sonter", email = "jsonter@gmail.com", picture = "https://lh4.googleusercontent.com/-Cbqcr6C_fTo/AAAAAAAAAAI/AAAAAAAAAIE/K697shQ1oo4/photo.jpg")
session.add(user1)

category1 = Category(name = "Category 1", user = user1)
session.add(category1)
category2 = Category(name = "Category 2", user = user1)
session.add(category2)
category3 = Category(name = "Category 3", user = user1)
session.add(category3)
category4 = Category(name = "Category 4", user = user1)
session.add(category3)
session.commit()

item1 = Item(name = "Item 1", description = "Description of item 1 which belongs to category 1", category = category1, user = user1, picture = "item1.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 2", description = "Description of item 2 which belongs to category 1", category = category1, user = user1, picture = "item2.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 3", description = "Description of item 3 which belongs to category 2", category = category2, user = user1, picture = "item3.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 4", description = "Description of item 4 which belongs to category 3", category = category3, user = user1, picture = "item4.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 5", description = "Description of item 5 which belongs to category 4", category = category4, user = user1, picture = "item5.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 6", description = "Description of item 6 which belongs to category 1", category = category1, user = user1, picture = "item6.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 7", description = "Description of item 7 which belongs to category 2", category = category2, user = user1, picture = "item7.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 8", description = "Description of item 8 which belongs to category 1", category = category1, user = user1, picture = "item8.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 9", description = "Description of item 9 which belongs to category 4", category = category4, user = user1, picture = "item9.jpg")
session.add(item1)
session.commit()

item1 = Item(name = "Item 10", description = "Description of item 10 which belongs to category 2", category = category2, user = user1, picture = "item10.jpg")
session.add(item1)
session.commit()


print "added database items!"
