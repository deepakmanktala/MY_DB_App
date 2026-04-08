from fontTools.misc.cython import returns

nums = [2,2,2,3,3,3,4,4,4,5,5,5,6,6,6,7,7,7,8,8,8,8,8]

######### DICT is to keep the unique elements and also the order
def remove_duplicates(nums):
    n = len(nums)
    dict = {}
    j = 0
    for i in range(0,n):

        dict[nums[i]]=0
    # return j
    for k in dict:
        nums[j] = k
        j += 1

    return j


######################### Optimal Solution #############

def remove_duplicates_optimal(nums):
    n = len(nums)
    if n == 1:
        return 1 ######## Handle the edge case using 2 pointers for a single element list

    i = 0
    j = i + 1

    while j < n:

        if nums[i] != nums[j]:
            i += 1 ### increment the left pointer and then swap with different element
            nums[i], nums[j] = nums[j], nums[i]
        j += 1

    return i+1


print(remove_duplicates_optimal(nums))
print(remove_duplicates(nums))