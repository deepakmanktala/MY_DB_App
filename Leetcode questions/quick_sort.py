nums = [4,9,3,2,5,6,7,3,2,1,10]

def partition(nums, low, high):
    pivot = nums[low]
    i = low
    j = high

    while i < j:
        while nums[i] <= pivot and i <= high - 1:
            i += 1
        while nums[j] >= pivot and j >= low+1:
            j -= 1

        if i < j:

    nums[low], nums[j] = nums[j], nums[low]
    return j


def quick_sort(nums, low, high):
    if low < high:
        partition_index = partition(nums, low, high)
        quick_sort(nums, low, partition_index-1)
        quick_sort(nums, partition_index+1, high)