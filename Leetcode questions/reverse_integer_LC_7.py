

def reverse(x):
    INT_MIN = -2**31
    INT_MAX = 2**31 - 1

    ## sign is stored separately , so that if its a negative number it can be use
    sign = -1 if x < 0 else 1

    x = abs(x)

    rev = 0 ## it is declared to hold teh reversed number

    while x != 0:
        last_digit = x % 10 ## This will give me the last digit

        ## now I have to remove the last digit from x

        x //= 10
        if rev > INT_MAX // 10 or (rev == INT_MAX // 10 and last_digit > 7):
            return 0

        ## Check for the overflow

        rev = rev * 10 + last_digit

    rev *= sign
    if rev < INT_MIN or rev > INT_MAX:
        return 0

    return rev

l = [-1,2,4,189898,-112121,12100,-4444]

for i in range(len(l)):

    # Access element
    # Time: O(1)
    x = l[i]

    # Call reverse function
    # Time: O(log x)
    result = reverse(x)

    # Print result
    # Time: O(1)
    print(f"{x} -> {result}")









print("################################# CORRECTED PROGRAM  ################################")

def reverse(x):

    # Define 32-bit integer limits
    # Time: O(1), Space: O(1)
    INT_MIN = -2**31
    INT_MAX = 2**31 - 1

    # Store sign separately
    # Time: O(1), Space: O(1)
    sign = -1 if x < 0 else 1

    # Work with absolute value
    # Time: O(1), Space: O(1)
    x = abs(x)

    # Variable to store reversed number
    # Time: O(1), Space: O(1)
    rev = 0


    # ------------------ MAIN LOOP ------------------
    # Loop runs until all digits are processed
    # If number has d digits → loop runs d times
    # Time Complexity: O(d) ≈ O(log10(x))
    while x != 0:

        # Extract last digit
        # Time: O(1), Space: O(1)
        last_digit = x % 10

        # Remove last digit from x
        # Time: O(1), Space: O(1)
        x //= 10

        # Build reversed number
        # Example: rev = 12 → becomes 123
        # Time: O(1), Space: O(1)
        rev = rev * 10 + last_digit


    # Apply sign AFTER full reversal
    # Time: O(1), Space: O(1)
    rev *= sign


    # ------------------ OVERFLOW CHECK ------------------
    # Check if result fits in 32-bit signed integer
    # Time: O(1), Space: O(1)
    if rev < INT_MIN or rev > INT_MAX:
        return 0


    # Return final result
    # Time: O(1), Space: O(1)
    return rev


# ------------------ DRIVER CODE ------------------

# List of numbers
# Time: O(1), Space: O(n)
l = [-1, 2, 4, 189898, -112121, 12100, -4444]


# Loop through list
# Time: O(n)
for i in range(len(l)):

    # Access element
    # Time: O(1)
    x = l[i]

    # Call reverse function
    # Time: O(log x)
    result = reverse(x)

    # Print result
    # Time: O(1)
    print(f"{x} -> {result}")