import copy
import time

user_session = {
    "username": "admin",
    "user_id":"101",
    "password": "",
    "email": "deepak.manktala@gmail.com",
    "profile": {
        "first_name": "Deepak",
            "last_name": "Manktala", "preferences":["dark_mode", "auto_play"]
                },
    "devices":["mobile", "laptop"]

}

shallow_copy = copy.copy(user_session)
shallow_copy["profile"]["preferences"].append("notfificatoins")
print(shallow_copy)

print(user_session["profile"]["preferences"])

print("##############################")

print(user_session["profile"]["preferences"][0])
print(user_session["profile"]["preferences"][1])

print("#########################################")


deep_copy = copy.deepcopy(user_session)
deep_copy["profile"]["preferences"].append("show_ads")
print(deep_copy)
print("#########################################")
print(user_session["profile"]["preferences"])







print("***************************")
print("***************************")

print("***************************")


time.sleep(0.1)
local_request["raking_context"]["features"].append(feature)

print(f"{name} local_request_features:{local_reque} ")



print("##############################################")
# standard params first, then *args, then **kwargs — always in this order
def full_function(required, *args, **kwargs):
    print(f"required = {required}")   # always must be provided
    print(f"args     = {args}")       # any extra positional args → tuple
    print(f"kwargs   = {kwargs}")     # any keyword args → dict

full_function("hello", 1, 2, 3, name="Deepak", city="Bangalore")
# Output:
# required = hello
# args     = (1, 2, 3)
# kwargs   = {'name': 'Deepak', 'city': 'Bangalore'}