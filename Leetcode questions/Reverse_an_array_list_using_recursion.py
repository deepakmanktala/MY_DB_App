l = [1,2,4,6,71,2,3,4,5,7,4,9,1,3,5,6,6]
m = []
print(len(l))

i = len(l) - 1

while i >= 0:

    m.append(l[i])
    i = i - 1
    print(m)

for i in l:

    print(i)
    # m.append(i)


############################ USING RECURSION ###########################
print ("############################ USING RECURSION ###########################")


def reverse_list(nums, left, right):
    if left >= right:
        return
    nums[left], nums[right] = nums[right], nums[left]
    # left += 1
    # right -= 1
    reverse_list(nums, left+1, right - 1)
    return nums

nums = [1,2,4,6,71,2,3,4,5,7,4,9,1,3,5,6,6]


print(reverse_list(nums, 0, 16))



print ("############################ USING RECURSION - THE APPROACHH ###########################")

'''
Python Reverse Inbuilt functions:

::-1
nums.reverse()
print(nums)

nums[::-1]


'''


'''
Reverse the list using SWAPS - let and right 
left = 0
right = len(nums) - 1

left pointer, right pointer = 0, len(nums) - 1
while left < right:

nums[left], nums[right] = nums[right], nums[left]
left += 1
right -= 1

'''
nums_2 = [1,2,4,6,7,3,34,4,4,4,4,7,7,1,1,1,1,3,2,3,4,5,7,4,9,1,3,5,6,6,1,2,3,4,6,6,6,6,6,6]

def reverse_list_2(nums_2, left, right):
    if left >= right:
        return

    nums_2[left], nums_2[right] = nums_2[right], nums_2[left]
    reverse_list_2(nums_2, left+1, right - 1)
    return nums_2

print(reverse_list_2(nums_2, 0, 39))















################### Iterative VErsion #########################
print("################################ Iterative Version #########################################")
#
# 🔥 Pro Tip
#
# 👉 Iterative version is better in interviews (no extra stack):

def reverse_list_3(nums):
    left, right = 0, len(nums)-1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
    return nums

print(reverse_list_3(nums))









###################FAANG Style ############################################################

# Define a list object and bind it to the variable name `nums_2`.
# Python allocates memory for 40 integers and stores references in a list structure.
# Time: O(N) for initialization
# Space: O(N) for storing N elements
nums_2 = [1, 2, 4, 6, 7, 3, 34, 4, 4, 4, 4, 7, 7, 1, 1, 1, 1, 3, 2, 3,
          4, 5, 7, 4, 9, 1, 3, 5, 6, 6, 1, 2, 3, 4, 6, 6, 6, 6, 6, 6]


# `def` → keyword to define a function object
# `reverse_list_2` → function name (identifier)
# `(nums_2, left, right)` → parameters:
#   nums_2 → reference to list object
#   left   → integer index (start pointer)
#   right  → integer index (end pointer)
def reverse_list_2(nums_2, left, right):

    # `if` → conditional branching keyword
    # `left >= right`:
    #   - `left` lookup → O(1)
    #   - `right` lookup → O(1)
    #   - `>=` comparison → O(1)
    # Total: O(1) time
    if left >= right:

        # `return nums_2`:
        # returns the reference to the same list object
        # No copying happens → only reference returned
        # Time: O(1)
        # Space: O(1)
        return nums_2


    # SWAP OPERATION (very important)

    # Left side:
    # nums_2[left], nums_2[right]
    # Python prepares a tuple of references

    # Right side:
    # nums_2[right], nums_2[left]
    # 1. nums_2[right] → index lookup → O(1)
    # 2. nums_2[left]  → index lookup → O(1)

    # Tuple packing (temporary):
    # (nums_2[right], nums_2[left]) → O(1) space

    # Assignment:
    # nums_2[left] = right_value
    # nums_2[right] = left_value

    # Entire swap:
    # Time: O(1)
    # Space: O(1)
    nums_2[left], nums_2[right] = nums_2[right], nums_2[left]


    # RECURSIVE CALL

    # left + 1:
    #   integer addition → O(1)
    # right - 1:
    #   integer subtraction → O(1)

    # reverse_list_2(...) call:
    #   - Python creates a NEW STACK FRAME
    #   - Stores:
    #       • current function context
    #       • parameters (nums_2 ref, left+1, right-1)
    #       • return address
    #   - Stack push → O(1)

    # IMPORTANT:
    # This is what causes O(N) space usage overall.

    # `return` here:
    # ensures the result propagates back up the call stack

    # Per call work: O(1)
    # Total calls: ~N/2
    # Total time: O(N)
    # Stack depth: O(N)
    return reverse_list_2(nums_2, left + 1, right - 1)


# FUNCTION CALL

# reverse_list_2(nums_2, 0, 39)
# Arguments:
#   nums_2 → reference passed (no copy) → O(1)
#   0, 39  → integer literals → O(1)

# print(...):
#   - converts list to string
#   - iterates over all elements
#   - Time: O(N)
#   - Space: O(N) for string representation
print(reverse_list_2(nums_2, 0, 39))



print("###################### ITERATIVE WHILE LOOP METHO #####################")

nums_5 = [1,2,4,5,6,7,7,7,7,7,7,7,8,9,1,2,3,4,5,6,7,8,9]

def reverse_list_5(nums_5):
    left, right = 0, len(nums_5)-1
    while left < right:
        nums_5[left], nums_5[right] = nums_5[right], nums_5[left]
        left += 1
        right -= 1
    return nums_5

print(reverse_list_5(nums_5))