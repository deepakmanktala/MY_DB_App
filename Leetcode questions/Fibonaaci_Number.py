# l = [0,1,1,2,3,5,8,13,21,34,55,89]

def create_fibonacci_recursive(n):
    # fib_number = n
    # # if n == 0:
    # #     return 0
    # # if n == 1:
    # #     return 1
    # if n >= 1:
    #     fib_number = create_fibonacci_recursive(n-1)+fib_number
    #     return fib_number
    if n == 0 or n == 1:
        return n
    return create_fibonacci_recursive(n - 1) + create_fibonacci_recursive(n - 2)

print(create_fibonacci_recursive(9))