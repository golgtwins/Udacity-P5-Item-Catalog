from sqlalchemy import *
from database_setup import Base, Category, CategoryItem
from sqlalchemy.orm import sessionmaker

# Seeding the database for testing

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Clear the tables
session.query(Category).delete()
session.query(CategoryItem).delete()

# Add categories
sample_categories = ['Eastern - Atlantic', 'Eastern - Metropolitan', 'Western - Central', 'Western -Pacific']

for category_name in sample_categories:
    category = Category(category_name)
    session.add(category)
session.commit()

# Add items
sample_items = {'Montreal': 1, 'Boston': 1, 'Toronto': 1,
                'NY Rangers': 2, 'Chicago': 3, 'Detroit': 1, 'New Jersey': 2,
                'Dallas': 3, 'Anaheim': 4, 'Edmonton': 4}

for item_title, item_category in sample_items.iteritems():
    item = CategoryItem(item_title, "Each Team Description Here.", item_category, 1)
    session.add(item)
session.commit()
