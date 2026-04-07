nums = [2,32,43-23,-23,-32,-32,-123,-32,133,3334,9843,2323,4343,2211,223,-323,-231]



############ Naive Method ##########################

# nums.sort()
# n = len(nums)
# print(nums[-2])
# print(nums[n-2])

largest = float("-inf")
second_largest = float("-inf")

for i in range (0,len(nums)):
    if nums[i] > largest:
        second_largest = largest
        third_largest = second_largest
        largest = nums[i]

    if nums[i] > second_largest and nums[i] != largest:
        second_largest = nums[i]

    if nums[i] > second_largest and nums[i] != largest and nums[i] != second_largest:
        third_largest = nums[i]
print(largest,second_largest, third_largest)




