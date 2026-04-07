################ Bubble SOrt Two Pointer Approach one form second last index, another one from first index j
'''
⚡ One-Line Intuition

👉 Bubble Sort =
"Push the largest element to the end in every pass"


🔍 How to Understand the Two Pointers (i and j)
👉 Pointer i (Outer Loop)
Moves from right → left
Represents the boundary of unsorted region
Everything after i is already sorted
👉 Pointer j (Inner Loop)
Moves from left → right
Compares adjacent elements
Performs swaps to push the largest element toward i+1
📌 Intuition Using One Pass

Example:

[5, 3, 2, 4]
First pass (i = 2)
j=0 → compare 5 & 3 → swap → [3,5,2,4]
j=1 → compare 5 & 2 → swap → [3,2,5,4]
j=2 → compare 5 & 4 → swap → [3,2,4,5]

👉 Now 5 is fixed at the end

🎯 Key Mental Model
|---- j scans ---->|   | sorted |
[ unsorted area    ]   [ done  ]
                ↑
                i boundary
j keeps pushing the largest element right
i keeps shrinking the unsorted region
⚡ One-Line Understanding

👉
j = worker (does comparisons & swaps)
i = boundary (marks sorted vs unsorted)




'''
nums = [32,32,4,43,43,43,2,32,4,6,465,75,7,76,67,867,67,67,67,6,4,46,5,64,64,6,645]

def bubble_sort(nums):
    for i in range(len(nums)-2, -1, -1):
        for j in range(0, i):
            if nums[j] > nums[j+1]:
                nums[j], nums[j+1] = nums[j+1], nums[j]

    return nums


print(bubble_sort(nums))







# Input list (unsorted)
nums = [32, 32, 4, 43, 43, 43, 2, 32, 4, 6, 465, 75, 7, 76, 67, 867, 67, 67, 67, 6, 4, 46, 5, 64, 64, 6, 645]
# Space: O(n) → storing input array


def bubble_sort(nums):
    """
    Bubble Sort using two pointers:
    - i → controls boundary from right side
    - j → scans from left to i

    Idea:
    -----
    Largest element "bubbles up" to the end in each iteration
    """

    # Outer loop: moves from second-last index to 0
    for i in range(len(nums) - 2, -1, -1):
        # len(nums) → O(1)
        # range(...) → O(1) to create iterator
        # Loop runs (n-1) times → O(n)

        # Inner loop: compare adjacent elements from start to i
        for j in range(0, i):
            # range(0, i) → O(1)
            # Loop runs i times → total across all i → O(n^2)

            # Compare current element with next element
            if nums[j] > nums[j + 1]:
                # Comparison → O(1)

                # Swap adjacent elements
                nums[j], nums[j + 1] = nums[j + 1], nums[j]
                # Swap → O(1)

    # Return sorted array
    return nums
    # Return → O(1)


# Function call + print result
print(bubble_sort(nums))
# Function call → O(n^2)
# print → O(n)











####################  Bubble SORT  If NO SWAPS ########################

nums = [21,324,43,43,55,43,232,32434,4343,4,89]

nums_sorted = [1,2,3,4,5,6,7,8,9]
def bubble_sort_Is_swap(nums):
    for i in range(len(nums) - 2, -1, -1):
        is_swap = False
        for j in range(0, i+1):
            if nums[j] > nums[j + 1]:
                nums[j], nums[j + 1] = nums[j + 1], nums[j]
                is_swap = True

        if is_swap == False:
            break

    return nums

print(bubble_sort_Is_swap(nums))

print(bubble_sort_Is_swap(nums_sorted))