nums = [3,43,23,2,1,56,78,44,42,232]

# return trus if its sorted, else return fals

def check_if_an_array_is_sorted(nums):
    n = len(nums)  # O(1)

    # Traverse entire array
    for i in range(0, n - 1):  # O(n)

        # If current element is greater than next → NOT sorted
        if nums[i] > nums[i + 1]:
            return False  # Early exit if unsorted

    # If loop completes → array is sorted
    return True


print(check_if_an_array_is_sorted(nums))



########### OR ##################

def check_if_an_array_is_sorted_again(nums):
    n = len(nums)

    for i in range(0, n - 1):

        if nums[i] <= nums[i + 1]:
            # ✅ This pair is correct → continue checking
            continue
        else:
            # ❌ Found a violation → not sorted
            return False

    # ✅ If loop finishes → all elements are in order
    return True


print(check_if_an_array_is_sorted_again(nums))