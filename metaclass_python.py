class User:
    pass

User = User();
User = type("User", (), {})
print(type(User))


class ModelMeta(type):

    def __new__(cls, name, bases, attrs):

        fields = []

        for key, value in attrs.items():
            if isinstance(value, Field):
                fields.append(key)

        attrs["_fields"] = fields

        return super().__new__(cls, name, bases, attrs)