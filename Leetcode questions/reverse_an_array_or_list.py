nums = [2,32,4,44,3,45,5,5,534,4343,433,22,211,22,223]

def reverse_array(nums):
    return nums[::-1]

def reverse_arra_2(nums):
    n = len(nums)
    temp_nums = [0] * n

    for i in range(len(nums)):
        temp_nums[i] = nums[n-i-1]
        print(temp_nums)

    for i in range(len(nums)):
        nums[i] = temp_nums[i]
        print(nums)

print(reverse_arra_2(nums))
