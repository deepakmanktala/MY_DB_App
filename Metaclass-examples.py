# Define a base Field class — acts as a marker/tag to identify database columns
class Field:
    pass  # No logic needed, just used to identify which attributes are "fields"

# Define a metaclass by inheriting from 'type' (Python's built-in metaclass)
# This gives ModelMeta the power to control how other classes are created
class ModelMeta(type):

    # __new__ is called automatically every time a new class is created using this metaclass
    # cls   = the metaclass itself (ModelMeta)
    # name  = the name of the class being created (e.g. "User")
    # bases = tuple of parent classes (e.g. (object,))
    # attrs = dictionary of all attributes and methods defined in the class body
    def __new__(cls, name, bases, attrs):

        # Create an empty list to collect names of attributes that are Field instances
        fields = []

        # Loop through every attribute defined inside the class body
        # key   = attribute name (e.g. "username", "email")
        # value = attribute value (e.g. Field(), or a regular method)
        for key, value in attrs.items():

            # Check if this attribute's value is an instance of Field
            # This filters out regular methods and non-field attributes
            if isinstance(value, Field):

                # If it is a Field, store its name into the fields list
                fields.append(key)

        # Inject a new attribute '_fields' into the class
        # This gives every class using this metaclass an automatic list of its field names
        attrs["_fields"] = fields

        # Call the parent class (type) __new__ to actually create and return the class
        # Without this line, the class would never be built
        return super().__new__(cls, name, bases, attrs)


# ── Step 1: Define User with only 'username' field ──────────────────────────
class User(metaclass=ModelMeta):  # Tell Python to use ModelMeta to create this class
    username = Field()            # 'username' is marked as a Field (a database column)

# Print _fields after Step 1 — ModelMeta automatically detected 'username'
print(f"Step 1  - Added 'username'       → _fields: {User._fields}")


# ── Step 2: Add 'email' field ───────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User — ModelMeta runs __new__ again fresh
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email — newly added

# Print _fields after Step 2 — now contains both username and email
print(f"Step 2  - Added 'email'          → _fields: {User._fields}")


# ── Step 3: Add 'age' field ─────────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again from scratch
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age — newly added

# Print _fields after Step 3 — now contains username, email, age
print(f"Step 3  - Added 'age'            → _fields: {User._fields}")


# ── Step 4: Add 'phone' field ───────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age
    phone    = Field()            # Field 4: phone — newly added

# Print _fields after Step 4
print(f"Step 4  - Added 'phone'          → _fields: {User._fields}")


# ── Step 5: Add 'address' field ─────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age
    phone    = Field()            # Field 4: phone
    address  = Field()            # Field 5: address — newly added

# Print _fields after Step 5
print(f"Step 5  - Added 'address'        → _fields: {User._fields}")


# ── Step 6: Add 'city' field ────────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age
    phone    = Field()            # Field 4: phone
    address  = Field()            # Field 5: address
    city     = Field()            # Field 6: city — newly added

# Print _fields after Step 6
print(f"Step 6  - Added 'city'           → _fields: {User._fields}")


# ── Step 7: Add 'country' field ─────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age
    phone    = Field()            # Field 4: phone
    address  = Field()            # Field 5: address
    city     = Field()            # Field 6: city
    country  = Field()            # Field 7: country — newly added

# Print _fields after Step 7
print(f"Step 7  - Added 'country'        → _fields: {User._fields}")


# ── Step 8: Add 'pincode' field ─────────────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username = Field()            # Field 1: username
    email    = Field()            # Field 2: email
    age      = Field()            # Field 3: age
    phone    = Field()            # Field 4: phone
    address  = Field()            # Field 5: address
    city     = Field()            # Field 6: city
    country  = Field()            # Field 7: country
    pincode  = Field()            # Field 8: pincode — newly added

# Print _fields after Step 8
print(f"Step 8  - Added 'pincode'        → _fields: {User._fields}")


# ── Step 9: Add 'date_of_birth' field ───────────────────────────────────────
class User(metaclass=ModelMeta):  # Redefine User again
    username      = Field()       # Field 1: username
    email         = Field()       # Field 2: email
    age           = Field()       # Field 3: age
    phone         = Field()       # Field 4: phone
    address       = Field()       # Field 5: address
    city          = Field()       # Field 6: city
    country       = Field()       # Field 7: country
    pincode       = Field()       # Field 8: pincode
    date_of_birth = Field()       # Field 9: date_of_birth — newly added

# Print _fields after Step 9
print(f"Step 9  - Added 'date_of_birth'  → _fields: {User._fields}")


# ── Step 10: Add 'is_active' field ──────────────────────────────────────────
class User(metaclass=ModelMeta):  # Final redefinition of User
    username      = Field()       # Field 1:  username
    email         = Field()       # Field 2:  email
    age           = Field()       # Field 3:  age
    phone         = Field()       # Field 4:  phone
    address       = Field()       # Field 5:  address
    city          = Field()       # Field 6:  city
    country       = Field()       # Field 7:  country
    pincode       = Field()       # Field 8:  pincode
    date_of_birth = Field()       # Field 9:  date_of_birth
    is_active     = Field()       # Field 10: is_active — newly added

# Print _fields after Step 10 — all 10 fields now present
print(f"Step 10 - Added 'is_active'      → _fields: {User._fields}")


# ── Final Summary ────────────────────────────────────────────────────────────
print("\n====== FINAL FIELDS IN User CLASS ======")

# Loop through _fields with an index starting at 1
# enumerate() gives both the index and the value of each item in the list
for i, field in enumerate(User._fields, start=1):

    # Print each field with its position number
    # :>2 means right-align the number in a width of 2 characters (for neat formatting)
    print(f"  Field {i:>2}: {field}")

# Print total count of fields using len() which returns the length of the list
print(f"\nTotal fields: {len(User._fields)}")