### https://claude.ai/chat/01782e47-c900-421f-86e4-6b9817fc3ade


def square(x):
    return x ** 2

suqare_lambda = lambda x: x ** 2


## The syntax is lambda <params>: <expression> — no return keyword needed, the expression result is returned automatically.

sum_1_lambda = lambda x, y : x * y + 1







# list of employee dicts — typical data shape from a DB or API response
employees = [
    {"name": "Alice",   "dept": "Engineering", "salary": 120000},
    {"name": "Bob",     "dept": "Product",     "salary": 95000},
    {"name": "Charlie", "dept": "Engineering", "salary": 140000},
    {"name": "Diana",   "dept": "Design",      "salary": 105000},
]

# sorted() needs a key function to know WHAT to sort by
# lambda e: e["salary"]  →  for each element e, extract its "salary" value
# sorted() uses that value to compare elements
by_salary = sorted(employees, key=lambda e: e["salary"])

# print each employee's name and salary in ascending order
for emp in by_salary:
    print(f"{emp['name']:10} → ₹{emp['salary']:,}")
# Output:
# Bob        → ₹95,000
# Diana      → ₹1,05,000
# Alice      → ₹1,20,000
# Charlie    → ₹1,40,000

# sort by MULTIPLE keys: primary = dept (alphabetical), secondary = salary (desc)
# lambda returns a TUPLE — Python compares tuples element by element
# -e["salary"] negates the value so higher salaries sort first within same dept
by_dept_then_salary = sorted(
    employees,
    key=lambda e: (e["dept"], -e["salary"])
)

for emp in by_dept_then_salary:
    print(f"{emp['dept']:15} {emp['name']:10} {emp['salary']:,}")
# Output:
# Design          Diana      1,05,000
# Engineering     Charlie    1,40,000
# Engineering     Alice      1,20,000
# Product         Bob        95,000





from functools import reduce   # reduce is not a builtin in Python 3, must import

# raw transaction data — could be millions of records in a real system
transactions = [
    {"id": "T1", "amount": 250.0,  "status": "success"},
    {"id": "T2", "amount": 89.5,   "status": "failed"},
    {"id": "T3", "amount": 4500.0, "status": "success"},
    {"id": "T4", "amount": 30.0,   "status": "success"},
    {"id": "T5", "amount": 1200.0, "status": "failed"},
]

# STEP 1: filter() keeps only elements where the lambda returns True
# lambda t: t["status"] == "success"  →  True only for successful transactions
successful = list(
    filter(lambda t: t["status"] == "success", transactions)
)
# successful now has T1, T3, T4

# STEP 2: map() transforms each element using the lambda
# lambda t: t["amount"]  →  extract just the numeric amount from each dict
amounts = list(
    map(lambda t: t["amount"], successful)
)
# amounts = [250.0, 4500.0, 30.0]

# STEP 3: reduce() collapses the list to a single value
# lambda acc, val: acc + val  →  running sum: starts at amounts[0], adds each next val
total = reduce(lambda acc, val: acc + val, amounts)

print(f"Successful transactions : {len(successful)}")   # 3
print(f"Total amount processed  : ₹{total:,.2f}")       # ₹4,780.00

# BONUS: entire pipeline in one expression — common in functional-style code
grand_total = reduce(
    lambda acc, val: acc + val,            # accumulate sum
    map(
        lambda t: t["amount"],             # extract amount
        filter(
            lambda t: t["status"] == "success",  # keep only successes
            transactions
        )
    )
)
print(f"One-liner total: ₹{grand_total:,.2f}")           # ₹4,780.00



# a factory function that RETURNS a lambda — this is a closure
# the returned lambda "closes over" the threshold variable
def make_threshold_checker(threshold):
    # the lambda is created here and captures 'threshold' from the enclosing scope
    # every call to make_threshold_checker creates a NEW lambda with its own threshold
    return lambda value: value >= threshold

# create specialised checker functions from the same factory
is_senior_engineer = make_threshold_checker(7)    # lambda value: value >= 7
is_staff_engineer   = make_threshold_checker(10)  # lambda value: value >= 10
is_principal        = make_threshold_checker(15)  # lambda value: value >= 15

# now use them like regular functions — clean, no if-else chains
yoe = 9    # years of experience

print(is_senior_engineer(yoe))   # True   (9 >= 7)
print(is_staff_engineer(yoe))    # False  (9 >= 10 → False)
print(is_principal(yoe))         # False  (9 >= 15 → False)

# store lambdas in a dict — acts as a dispatch table (replaces if/elif chains)
# each key maps to a lambda that applies a different discount rate
discount_rules = {
    "student":    lambda price: price * 0.50,   # 50% off
    "employee":   lambda price: price * 0.20,   # 20% off
    "premium":    lambda price: price * 0.10,   # 10% off
    "no_discount": lambda price: price * 1.00,  # no discount
}

def apply_discount(price, user_type):
    # look up the right lambda by user_type, fall back to no_discount
    rule = discount_rules.get(user_type, discount_rules["no_discount"])
    return rule(price)    # call whichever lambda was selected

print(apply_discount(1000, "student"))   # 500.0
print(apply_discount(1000, "employee"))  # 800.0
print(apply_discount(1000, "vip"))       # 1000.0  (fallback)