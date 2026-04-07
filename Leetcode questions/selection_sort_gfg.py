"""
################### SELECTION SORT is to have i and j --> Two Pointers and a Minimum Index maintained ##########################)


################# Selection SORT scan -> select minimum -> swap once ###################################


###########################  Selection Sort = “Find the smallest and put it in front.” ###############################
Bubble sort
compares adjacent elements
many swaps
largest values move right gradually
Selection sort
scans whole unsorted region
finds one minimum
does one swap per pass

That “one swap per pass” is a major property of selection sort.



Selection Sort: Core Idea

Selection sort works like this:

split the array into 2 parts:
left side = sorted part
right side = unsorted part
in every pass:
find the smallest value in the unsorted part
swap it with the first element of the unsorted part

So instead of bubbling values through adjacent swaps, like bubble sort, selection sort does this:

scan -> select minimum -> swap once

That is the main idea.

Mental Model

Think of it like arranging playing cards:

at position i, you ask:
“what is the smallest card from here to the end?”
once found, place it at i
move i one step right
repeat
Pointer Roles in Selection Sort
i pointer

i is the boundary of the sorted and unsorted regions.

everything before i is already sorted
everything from i onward is still unsorted
i tells us: “this is the position where the next smallest element should go”
j pointer

j scans the unsorted part.

starts from i + 1
moves to the end
compares elements to find the current minimum
min_index

This is the most important helper variable.

stores the index of the smallest element found so far
starts as i
gets updated whenever we find a smaller value
Visual Layout
Initial array:
[ 32, 12, 7, 25, 3, 18 ]

Pass 1:
  i
  ↓
[ 32, 12, 7, 25, 3, 18 ]
        ↑--------------↑
              j scans
min_index finally becomes index of 3

Swap arr[i] with arr[min_index]

[ 3, 12, 7, 25, 32, 18 ]


Pass 2:
      i
      ↓
[ 3, 12, 7, 25, 32, 18 ]
          ↑-----------↑
             j scans
min_index becomes index of 7

Swap

[ 3, 7, 12, 25, 32, 18 ]
Very Important Difference from Bubble Sort
Bubble sort
compares adjacent elements
many swaps
largest values move right gradually
Selection sort
scans whole unsorted region
finds one minimum
does one swap per pass

That “one swap per pass” is a major property of selection sort.

Correct Python Program with Detailed Comments
# Input array
arr = [32, 12, 7, 25, 3, 18, 9, 1]

def selection_sort(arr):
    """
Selection Sort in ascending order.

Idea:
- For each index i, assume arr[i] is the minimum
- Use j to scan the remaining unsorted part
- Update min_index whenever a smaller element is found
- After scan completes, swap arr[i] with arr[min_index]

This sorts the array in-place.
"""

# Get the total number of elements in the array
n = len(arr)                     # Time: O(1), Space: O(1)

# Outer loop:
# i marks the first index of the unsorted region
# Everything before i is already sorted
for i in range(n):               # Loop runs n times -> O(n)

    # Assume the current position i has the minimum element
    min_index = i                # Time: O(1), Space: O(1)

    # Inner loop:
    # j scans the unsorted region to find the actual minimum
    for j in range(i + 1, n):    # Total over all passes -> O(n^2)

        # Compare current scanned element with current minimum
        if arr[j] < arr[min_index]:   # Comparison -> O(1)

            # Found a smaller element, so update min_index
            min_index = j             # Time: O(1)

    # After the inner loop finishes:
    # min_index contains the index of the smallest element
    # in the unsorted region arr[i...n-1]

    # Swap current position i with the minimum found
    arr[i], arr[min_index] = arr[min_index], arr[i]   # Time: O(1)

# Return the sorted array
return arr                           # Time: O(1)


print(selection_sort(arr))
Flow of the Algorithm
Start
↓
Set i = 0
↓
Assume min_index = i
↓
Move j from i+1 to n-1
↓
Is arr[j] < arr[min_index] ?
├── Yes -> update min_index = j
└── No  -> continue scanning
↓
After j finishes, swap arr[i] and arr[min_index]
↓
Move i to next position
↓
Repeat until array ends
↓
Sorted

This matches the standard selection-sort flow shown in common flow diagrams.

Step-by-Step Dry Run

Let’s dry run this array:

[29, 10, 14, 37, 13]
Pass 1

i = 0
Assume minimum is at index 0 -> value = 29

j scans from 1 to 4:

compare 10 with 29 -> smaller -> min_index = 1
compare 14 with 10 -> no change
compare 37 with 10 -> no change
compare 13 with 10 -> no change

Minimum found = 10 at index 1

Swap arr[0] and arr[1]

Array becomes:

[10, 29, 14, 37, 13]
Pass 2

i = 1
Assume minimum = 29

j scans from 2 to 4:

compare 14 with 29 -> smaller -> min_index = 2
compare 37 with 14 -> no change
compare 13 with 14 -> smaller -> min_index = 4

Swap arr[1] and arr[4]

Array becomes:

[10, 13, 14, 37, 29]
Pass 3

i = 2
Assume minimum = 14

j scans from 3 to 4:

compare 37 with 14 -> no change
compare 29 with 14 -> no change

Swap with itself

Array remains:

[10, 13, 14, 37, 29]
Pass 4

i = 3
Assume minimum = 37

j scans from 4 to 4:

compare 29 with 37 -> smaller -> min_index = 4

Swap

Array becomes:

[10, 13, 14, 29, 37]

Sorted.

Pointer Visualization in One Pass

Take this array:

[ 20, 12, 10, 15, 2 ]
First pass
i = 0
min_index = 0

[ 20, 12, 10, 15, 2 ]
↑
i, min_index initially

j scans:
  ↑
  12 < 20 -> min_index = 1

[ 20, 12, 10, 15, 2 ]
  ↑
min_index

      ↑
      10 < 12 -> min_index = 2

[ 20, 12, 10, 15, 2 ]
      ↑
  min_index

              ↑
              2 < 10 -> min_index = 4

Swap arr[0] and arr[4]

[ 2, 12, 10, 15, 20 ]

This is exactly the type of progression shown in the visual selection-sort diagrams above.

Time Complexity
Outer loop

Runs n times.

Inner loop

For each i, j scans the remaining part.

Total comparisons:

(n - 1) + (n - 2) + (n - 3) + ... + 1
= n(n - 1) / 2
= O(n^2)
Swaps

At most one swap per outer iteration:

O(n)
Final Time Complexity
Best case: O(n^2)
Average case: O(n^2)
Worst case: O(n^2)
Important

Even if the array is already sorted, selection sort still scans the remaining array fully, so best case is still O(n^2).

Space Complexity

Selection sort is in-place.

no extra array used
only a few variables: n, i, j, min_index

So:

Space complexity: O(1)
Why Selection Sort Is Called “Selection” Sort

Because in each pass it selects the smallest element from the unsorted region and places it in the correct spot.

Not because it swaps constantly.
Not because it compares adjacent elements.
It is specifically about selection of the minimum.

Is Selection Sort Stable?

Standard selection sort is not stable.

Example:

[5a, 5b, 3]

After sorting, one possible result is:

[3, 5b, 5a]

The relative order of equal elements changed.

So:

standard selection sort -> unstable
Is Selection Sort In-Place?

Yes.

It modifies the original array directly.

So:

in-place -> yes
stable -> no
Why It Is Still Taught

Even though it is slow for large arrays, it is useful because:

very easy to understand
teaches nested-loop reasoning
teaches “sorted vs unsorted partition”
does fewer swaps than bubble sort
useful for interviews and fundamentals
Bubble Sort vs Selection Sort
Bubble sort
adjacent comparisons
many swaps
best case can become O(n) with optimization
stable
Selection sort
global minimum search in unsorted part
one swap per pass
best case still O(n^2)
not stable
Common Mistake

This is the wrong way:

if arr[j] < arr[min_index]:
min_index = j
arr[i], arr[min_index] = arr[min_index], arr[i]   # wrong here

Why wrong?

Because you are swapping while still scanning.
Selection sort must first complete the scan, then swap once.

Correct flow:

find min_index completely
then swap once
Descending Selection Sort

For descending order, the logic is the same, except:

find the maximum instead of the minimum
swap it into position i
def selection_sort_desc(arr):
n = len(arr)

for i in range(n):
    max_index = i
    for j in range(i + 1, n):
        if arr[j] > arr[max_index]:
            max_index = j
    arr[i], arr[max_index] = arr[max_index], arr[i]

return arr
Tiny Interview Summary

Selection sort:

divides array into sorted and unsorted regions
uses i as current placement index
uses j to scan for the smallest value
tracks smallest value with min_index
swaps once per pass
time: O(n^2)
space: O(1)
in-place: yes
stable: no
Super Simple Memory Trick

Selection Sort = “Find the smallest and put it in front.”

If you want, I can turn this into a single mega program containing:

ascending selection sort
descending selection sort
bubble sort comparison
dry-run print statements for every pass
interview notes inside comments






"""








"""
===========================================================
        SELECTION SORT (ASCENDING + DESCENDING)
===========================================================

Core Idea:
----------
Selection Sort divides the array into two parts:
1. Sorted portion (left side)
2. Unsorted portion (right side)

At each step:
- Find MIN (for ascending) OR MAX (for descending)
- Swap it with the current position

IMPORTANT:
----------
✔ Only ONE swap per outer loop iteration
✔ In-place sorting (no extra memory used)

Time Complexity:
---------------
Worst Case:  O(n^2)
Best Case:   O(n^2)  (no optimization possible)
Average:     O(n^2)

Space Complexity:
----------------
O(1) → In-place (no extra space)

===========================================================
"""


# -------------------------------
# ASCENDING SELECTION SORT
# -------------------------------
def selection_sort_ascending(nums):
    """
    Sorts the list in ascending order using selection sort
    """

    # Step 1: Get length of list
    n = len(nums)
    # Time: O(1), Space: O(1)

    # Step 2: Traverse entire array
    for i in range(n):
        # Runs n times → O(n)

        # Assume current index has minimum value
        min_index = i
        # Time: O(1)

        # Step 3: Find minimum in remaining unsorted array
        for j in range(i + 1, n):
            # Runs (n-i-1) times → overall O(n^2)

            # Compare current element with current minimum
            if nums[j] < nums[min_index]:
                # Comparison → O(1)

                # Update minimum index
                min_index = j
                # Time: O(1)

        # Step 4: Swap AFTER inner loop completes
        nums[i], nums[min_index] = nums[min_index], nums[i]
        # Swap → O(1)

    return nums
    # Return sorted array → O(1)


# -------------------------------
# DESCENDING SELECTION SORT
# -------------------------------
def selection_sort_descending(nums):
    """
    Sorts the list in descending order using selection sort
    """

    # Step 1: Get length of list
    n = len(nums)
    # Time: O(1)

    # Step 2: Traverse array
    for i in range(n):
        # O(n)

        # Assume current index has maximum value
        max_index = i
        # Time: O(1)

        # Step 3: Find maximum in remaining array
        for j in range(i + 1, n):
            # O(n^2 overall)

            # Compare current element with current maximum
            if nums[j] > nums[max_index]:
                # O(1)

                # Update maximum index
                max_index = j
                # O(1)

        # Step 4: Swap AFTER inner loop completes
        nums[i], nums[max_index] = nums[max_index], nums[i]
        # O(1)

    return nums


# -------------------------------
# MAIN DRIVER CODE
# -------------------------------

# Original input list
nums = [32, 4354, 5454, 32, 12, 3, 45, 7, 8, 9, 1, 2, 34, 5, 12, 3, 4, 6, 7]

# Make copies so original list is preserved
ascending_list = nums.copy()      # O(n) space
descending_list = nums.copy()     # O(n) space

# Perform sorting
sorted_asc = selection_sort_ascending(ascending_list)
sorted_desc = selection_sort_descending(descending_list)

# Output results
print("Original List  :", nums)
print("Ascending Sort :", sorted_asc)
print("Descending Sort:", sorted_desc)


"""
===========================================================
            OVERALL COMPLEXITY ANALYSIS
===========================================================

1. Outer Loop runs → n times
2. Inner Loop runs → (n-1), (n-2), ..., 1

Total comparisons:
= n(n-1)/2 ≈ O(n^2)

Total swaps:
= O(n) → Only one swap per iteration

===========================================================
WHY SELECTION SORT?
===========================================================

✔ Minimal swaps → useful in:
   - Embedded systems
   - Flash memory (write expensive)

✔ Simple logic → easy to implement

❌ Not efficient for large datasets

===========================================================
INTERVIEW PRO TIP 🚀
===========================================================

If asked:
"Why not use selection sort in production?"

Answer:
- Use Python's built-in sort → Timsort (O(n log n))
- Selection sort is mainly for learning & small datasets

===========================================================
"""