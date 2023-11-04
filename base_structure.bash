#!/bin/bash
mkdir irony
# Create inner package files
mkdir irony/irony
touch irony/irony/__init__.py
touch irony/irony/main.py
touch irony/irony/config.py
touch irony/irony/db.py

# Create models folder and files
mkdir irony/irony/models
touch irony/irony/models/__init__.py
touch irony/irony/models/user.py 
touch irony/irony/models/item.py

# Create routers folder and files
mkdir irony/irony/routers  
touch irony/irony/routers/__init__.py
touch irony/irony/routers/users.py
touch irony/irony/routers/items.py

# Additional folders and files  
mkdir irony/tests
mkdir irony/scripts
touch irony/README.md  
touch irony/requirements.txt
touch irony/setup.py