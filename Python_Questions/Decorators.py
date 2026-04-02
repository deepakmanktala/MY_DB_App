import functools

def my_decortaor_deep(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("Something is happening before this function")
        func(*args, **kwargs)
        print("Something is happening after this function")
    return wrapper

@my_decortaor_deep
def say_hello(name):
    print(f"Hello, {name}!")

say_hello("Deepak")

# Step 1: understand what a decorator IS before using @
# A decorator is just a function that takes a function and returns a function

def my_decorator(func):              # accepts the original function as argument
    @functools.wraps(func)           # preserves original function's __name__, __doc__
    def wrapper(*args, **kwargs):    # wrapper accepts any arguments the original takes
        print("-- before the function runs --")   # code that runs BEFORE
        result = func(*args, **kwargs)            # call the original function
        print("-- after the function runs --")    # code that runs AFTER
        return result                             # return whatever original returned
    return wrapper                   # return the wrapper, NOT the result of calling it

# Step 2: manually apply the decorator (what @ does under the hood)
def say_hello(name):
    print(f"Hello, {name}!")

say_hello = my_decorator(say_hello)  # replace say_hello with the wrapped version
say_hello("Deepak")
# Output:
# -- before the function runs --
# Hello, Deepak!
# -- after the function runs --

# Step 3: the clean @ syntax does exactly the same thing
@my_decorator                        # equivalent to: greet = my_decorator(greet)
def greet(name):
    print(f"Good morning, {name}!")

greet("Deepak")                      # same output pattern as above










import functools

# Step 1: understand what a decorator IS before using @
# A decorator is just a function that takes a function and returns a function

def my_decorator(func):              # accepts the original function as argument
    @functools.wraps(func)           # preserves original function's __name__, __doc__
    def wrapper(*args, **kwargs):    # wrapper accepts any arguments the original takes
        print("-- before the function runs --")   # code that runs BEFORE
        result = func(*args, **kwargs)            # call the original function
        print("-- after the function runs --")    # code that runs AFTER
        return result                             # return whatever original returned
    return wrapper                   # return the wrapper, NOT the result of calling it

# Step 2: manually apply the decorator (what @ does under the hood)
def say_hello(name):
    print(f"Hello, {name}!")

say_hello = my_decorator(say_hello)  # replace say_hello with the wrapped version
say_hello("Deepak")
# Output:
# -- before the function runs --
# Hello, Deepak!
# -- after the function runs --

# Step 3: the clean @ syntax does exactly the same thing
@my_decorator                        # equivalent to: greet = my_decorator(greet)
def greet(name):
    print(f"Good morning, {name}!")

greet("Deepak")                      # same output pattern as above

# Decorator Example 2 — Timer decorator (measure execution time)
import functools
import time

def timer(func):                         # decorator factory — takes the function
    @functools.wraps(func)               # copy __name__ and __doc__ to wrapper
    def wrapper(*args, **kwargs):        # wrapper accepts any signature
        start = time.perf_counter()      # record start time with high precision
        result = func(*args, **kwargs)   # run the actual function
        end   = time.perf_counter()      # record end time
        elapsed = end - start            # compute elapsed seconds
        print(f"[timer] {func.__name__} took {elapsed:.6f}s")  # log it
        return result                    # return the original result unchanged
    return wrapper                       # return wrapper, not the result

@timer                                   # apply timer decorator
def process_transactions(records):
    """Simulate processing a batch of payment records."""
    total = 0
    for r in records:                    # loop through each record
        total += r['amount']             # accumulate total
    time.sleep(0.01)                     # simulate I/O delay
    return total

records = [{'amount': 250}, {'amount': 1200}, {'amount': 750}]
total = process_transactions(records)
print(f"Total: ₹{total}")
# [timer] process_transactions took 0.010243s
# Total: ₹2200

# The original function is completely unmodified — the timer is added externally
print(process_transactions.__name__)     # 'process_transactions' (not 'wrapper')
# because of @functools.wraps

# Decorator Example 3 — Decorator with arguments (decorator factory)
# When you need to pass parameters to a decorator, you add one more layer of nesting — a factory function that returns the actual decorator.
import functools

def retry(max_attempts=3, delay=1.0):
    """
    Decorator factory — returns a decorator that retries a function
    up to max_attempts times if it raises an exception.
    """
    def decorator(func):                      # the actual decorator
        @functools.wraps(func)
        def wrapper(*args, **kwargs):         # the wrapper around the function
            last_exception = None
            for attempt in range(1, max_attempts + 1):   # try up to max times
                try:
                    return func(*args, **kwargs)          # try calling the function
                except Exception as e:
                    last_exception = e                    # remember the error
                    print(f"[retry] attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:            # if not the last attempt
                        import time
                        time.sleep(delay)                 # wait before retrying
            raise last_exception                         # all retries exhausted
        return wrapper
    return decorator                          # return the decorator

# @retry(max_attempts=3, delay=0.5) means:
# connect_to_issuer = retry(max_attempts=3, delay=0.5)(connect_to_issuer)
@retry(max_attempts=3, delay=0.5)
def connect_to_issuer(host):
    """Simulate a network call that might fail."""
    import random
    if random.random() < 0.7:                # 70% chance of failure
        raise ConnectionError(f"Could not reach {host}")
    return f"Connected to {host}"

try:
    result = connect_to_issuer("issuer.bank.com")
    print(result)
except ConnectionError:
    print("All retries exhausted — transaction declined")

# Decorator Example 4 — Stacking multiple decorators
import functools, time

def logger(func):
    """Logs function entry and exit."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG]   calling {func.__name__} with args={args} kwargs={kwargs}")
        result = func(*args, **kwargs)       # call the function
        print(f"[LOG]   {func.__name__} returned {result}")
        return result
    return wrapper

def timer(func):
    """Times function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start  = time.perf_counter()
        result = func(*args, **kwargs)       # call the function
        end    = time.perf_counter()
        print(f"[TIME]  {func.__name__} took {end - start:.4f}s")
        return result
    return wrapper

def validate_positive(func):
    """Ensures all numeric arguments are positive."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, (int, float)) and arg <= 0:   # check each arg
                raise ValueError(f"Argument {arg} must be positive")
        return func(*args, **kwargs)         # proceed only if all valid
    return wrapper

# Stacking: decorators apply BOTTOM UP during decoration
# but execute TOP DOWN during the call
# @logger      → applied last  → outermost layer → runs first
# @timer       → applied second
# @validate_positive → applied first → innermost layer → runs last
@logger
@timer
@validate_positive
def calculate_interest(principal, rate, years):
    """Compute compound interest."""
    return principal * ((1 + rate) ** years)  # compound interest formula

result = calculate_interest(10000, 0.08, 5)
# [LOG]   calling calculate_interest with args=(10000, 0.08, 5) kwargs={}
# [TIME]  calculate_interest took 0.0000s
# [LOG]   calculate_interest returned 14693.28...

# What happens with invalid input:
try:
    calculate_interest(-1000, 0.08, 5)    # negative principal
except ValueError as e:
    print(f"Validation failed: {e}")      # Argument -1000 must be positive

# Decorator Example 5 — Class-based decorator and real-world @property
# pythonimport functools

# ── A: Class-based decorator — useful when you need state ─────────
class CallCounter:
    """Decorator implemented as a class — tracks how many times a function is called."""

    def __init__(self, func):            # __init__ receives the function
        functools.update_wrapper(self, func)  # copy func metadata to self
        self.func       = func           # store the original function
        self.call_count = 0              # initialise counter (state persists!)

    def __call__(self, *args, **kwargs): # __call__ makes the instance callable
        self.call_count += 1             # increment counter on every call
        print(f"[count] {self.func.__name__} has been called {self.call_count} times")
        return self.func(*args, **kwargs)  # call original and return result

@CallCounter                             # CallCounter(process_payment) called here
def process_payment(amount):
    return f"Processed ₹{amount}"

process_payment(100)    # called 1 times
process_payment(200)    # called 2 times
process_payment(300)    # called 3 times
print(process_payment.call_count)  # 3  — state is accessible!

# ── B: Python's built-in @property decorator ─────────────────────
class BankAccount:
    def __init__(self, owner, balance):
        self.owner    = owner            # public attribute
        self._balance = balance          # private by convention (leading _)

    @property                            # makes balance a read-only computed attribute
    def balance(self):
        """Getter — called when you access account.balance."""
        return self._balance             # returns the private value

    @balance.setter                      # setter — called when you assign account.balance = x
    def balance(self, amount):
        if amount < 0:                   # validate before allowing the change
            raise ValueError("Balance cannot be negative")
        self._balance = amount           # update private value only if valid

    @property
    def summary(self):                   # computed property — no setter needed
        return f"{self.owner}: ₹{self._balance:,.2f}"

acc = BankAccount("Deepak", 50000)
print(acc.balance)          # 50000   — calls the getter
acc.balance = 75000         # calls the setter — validated before setting
print(acc.summary)          # Deepak: ₹75,000.00
acc.balance = 10000          # raises ValueError: Balance cannot be negative