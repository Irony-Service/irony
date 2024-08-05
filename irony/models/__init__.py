# Here, we've imported item, user from the same package (models) in the __init__.py file.
# This means that when you import the models from other parts of your project, item, user will also be accessible without needing to import it explicitly.
from . import user
from .contact_details import ContactDetails
