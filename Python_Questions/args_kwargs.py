## args keep the arguments into tuple
## kwargs keeps the arguments into a dictionary

## args example

# *args collects all positional arguments into a tuple called 'numbers'

def add_all(*numbers):
    total = 0
    for n in numbers:
        total += n
    return total

print(add_all(1,2,3,4,5))
print(add_all(1,2,3,4,5,10,1323))
print(add_all(5))

def log_messages(level, *messages):
    # 'level' is a regular param — it must always be provided first
    # 'messages' captures everything else as a tuple

    for msg in messages:
        print(f"{[level]} {msg}")  # format and print each one

# first arg goes to 'level', the rest pack into 'messages'
log_messages("INFO", "Server_started", "at port number 8080")

log_messages("Error", "Got an Error", "Disk Full")





def multiply_all(*numbers):
    total = 1
    for n in numbers:
        total *= n
    return total
print(multiply_all(1,2,3,4,5))
print(multiply_all(5))
numbers = [1,2,3,4,5,10,120]
print(multiply_all(*numbers))
print(multiply_all(*numbers))
print(multiply_all(*numbers))
print(multiply_all(10,20))
print(multiply_all(10,20))
print(multiply_all(10,20))







print('''
"################ Let's Get to **kwargs Now ###########################################


############### Let's Get to **kwargs Now ###########################################

"''')


def create_profile(**details):
    print("-------user profile-----------")
    for key, value in details.items():
        print(f"{key}: {value}")

create_profile(name="Deepak", post = "manager", company = "Verifone")






print('''
Example 2: Build an HTML tag dynamically
python# tag is a regular param; **attrs catches all keyword args as a dict

''')


def make_tag(tag, content, **attrs):
    attr_string = ""
    for key, value in attrs.items():
        attr_string += f"{key}: {value}; "
    return f"<{tag} {attr_string}>{content}</{tag}>"

print(make_tag("a", "Clcik Me", href="/home", class="btn", id ="nav_link"))
