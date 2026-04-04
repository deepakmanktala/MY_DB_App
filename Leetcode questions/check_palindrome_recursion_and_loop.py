# ---------------------- INPUT STRINGS ----------------------

# Assign string to variable
# Time Complexity  : O(1)
# Space Complexity : O(n) where n = length of string
word_1 = 'malayalam'

# Time: O(1), Space: O(n)
word_2 = 'nitin'

# Time: O(1), Space: O(n)
word_3 = 'anabalannalabana'


# ---------------------- LIST CREATION ----------------------

# Create empty list to store words
# Time Complexity  : O(1)
# Space Complexity : O(1) initially
l = []

# Append word_1 to list
# Time Complexity  : O(1) amortized
# Space Complexity : O(1) additional (reference stored)
l.append(word_1)

# Append word_2
# Time Complexity  : O(1) amortized
# Space Complexity : O(1)
l.append(word_2)

# Append word_3
# Time Complexity  : O(1) amortized
# Space Complexity : O(1)
l.append(word_3)


# Print list
# Time Complexity  : O(k) where k = total characters printed
# Space Complexity : O(1)
print(l)


# ---------------------- PALINDROME FUNCTION ----------------------

def isPalindrome(s):

    # Get length of string
    # Time Complexity  : O(1)
    # Space Complexity : O(1)
    n = len(s)

    # Initialize left pointer (start of string)
    # Time Complexity  : O(1)
    # Space Complexity : O(1)
    left = 0

    # Initialize right pointer (end of string)
    # Time Complexity  : O(1)
    # Space Complexity : O(1)
    right = n - 1


    # ---------------------- TWO POINTER LOOP ----------------------

    # Loop until pointers meet in middle
    # Runs approximately n/2 times → O(n)
    while left < right:

        # Compare characters at left and right
        # s[left] and s[right] indexing → O(1)
        # Comparison → O(1)
        if s[left] != s[right]:

            # Print result (string formatting)
            # Time Complexity  : O(n) (printing full string)
            # Space Complexity : O(1)
            print(s, ' is not a palindrome')

            # Return False → exits function immediately
            # Time Complexity  : O(1)
            # Space Complexity : O(1)
            return False

        # Move left pointer forward
        # Time Complexity  : O(1)
        # Space Complexity : O(1)
        left += 1

        # Move right pointer backward
        # Time Complexity  : O(1)
        # Space Complexity : O(1)
        right -= 1


    # If loop completes → string is palindrome

    # Print result
    # Time Complexity  : O(n)
    # Space Complexity : O(1)
    print(s, ' is a palindrome')

    # Return True
    # Time Complexity  : O(1)
    # Space Complexity : O(1)
    return True


# ---------------------- DRIVER LOOP ----------------------

# Iterate through list of words
# Time Complexity  : O(m) where m = number of words
for i in range(0, len(l)):

    # Print current word
    # Time Complexity  : O(n) (depends on string length)
    # Space Complexity : O(1)
    print(l[i])

    # Call palindrome function
    # Time Complexity  : O(n) per word
    # Space Complexity : O(1)
    isPalindrome(l[i])


# ---------------------- OVERALL COMPLEXITY ----------------------

# Let:
# m = number of strings
# n = average length of each string

# Total Time Complexity:
#   = O(m * n)
#   (each string takes O(n) to check palindrome)

# Total Space Complexity:
#   = O(1) auxiliary (no extra memory used)
#   = O(total input size) for storing strings

# ---------------------- KEY INSIGHT ----------------------

# This is an optimal palindrome check:
# ✔ Uses two pointers
# ✔ No extra memory
# ✔ Stops early on mismatch (best-case faster)

# This pattern is heavily used in:
# - String problems (FAANG)
# - Two pointer techniques
# - Sliding window problems




print("##################### Solve Via Recursion ###################################")

def isPalindrome_recursive(s, left, right):
    if left >= right:
        return True
    if s[left] != s[right]:
        print(s, ' is not a palindrome')
        return False
    return isPalindrome_recursive(s, left + 1,  right -1 )
    n = len(s)
    left = 0
#
# for i in range(0, len(l)):
#
#     # Print current word
#     # Time Complexity  : O(n) (depends on string length)
#     # Space Complexity : O(1)
#     print(l[i])
#
#     # Call palindrome function
#     # Time Complexity  : O(n) per word
#     # Space Complexity : O(1)
#     isPalindrome(l[i])
#

###### Time COmplexity TC = O(N/2) ~ O(N), Space Complexity is O(N/2) which is ~  O(N)   #######################
######                                                                                   #######################
print(isPalindrome_recursive(word_1, 0, len(word_1) - 1))
print(isPalindrome_recursive(word_2, 0, len(word_2) - 1))
print(isPalindrome_recursive(word_3, 0, len(word_3) - 1))