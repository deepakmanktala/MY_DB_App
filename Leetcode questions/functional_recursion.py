############### FUNCTIONAL RECURSION ############
''' CREATE THE FLOW, CREATE THE BASE CONDITION'''
''' ALWAYS HAVE THE BASE FUNCTION for exampls f(1) is 1, N + f(N) '''

def func(N):
    if N == 1:
        return 1
    return N + func(N-1)

func(10)

print(func(10))




def func_2(N):
    # Base case:
    # If N becomes 1, stop recursion and return 1.
    # Time: O(1)
    # Extra space used in this line: O(1)
    if N == 1:
        return 1

    # Recursive case:
    # First, Python must evaluate func(N - 1).
    # Then it adds N to the returned value.
    #
    # N - 1         -> O(1)
    # function call -> creates one new stack frame
    # addition      -> O(1)
    #
    # Work done in THIS call itself is O(1),
    # but total work across all recursive calls becomes O(N).
    return N + func(N - 1)


# This computes the result but does not print or store it.
# So the value is discarded.
# Time: O(N)
# Space: O(N) because of recursion stack
func_2(10)

# This computes again from scratch and prints the result.
# Time: O(N)
# Space: O(N)
print(func_2(10))