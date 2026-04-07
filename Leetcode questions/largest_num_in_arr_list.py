############Time COmplexity O(N)

############## Space Complexity O (1)

nums = [1,4,5,7,-97,0,-9,21,--673,126,12,121212,1232323,121232,1232,33221,212,323-128832,-3267,2321]


def largest(nums):
    n = len(nums)
    largest = nums[0]

    for i in range(0,n):
        largest =  max(nums[i],largest)
    return largest

print(largest(nums))










########## DO NOT USE MAX ############

nums_2 = [-12,-1223,-1223,-121213,1212,32,4354,545,454,65,565,2323,43423,878,899,89878,875,655,45,4457]

largest_2 = nums_2[0]
n2 = len(nums_2)

for i in range(0,n2):
    if nums_2[i] > largest_2:
        largest_2 = nums_2[i]
    else:
        pass
print(largest_2)











############ Method 3 ###########################


nums_4 = [23,4,5,6,65,4,4,5,54,534,3-323,43-43,-43,-34,54,-453,34,-3,3434-434,-345534, -324,234234,432,42343,43,4322,43423]

largest_4 = float("-inf")

for i in nums_4:
    if i > largest_4:
        largest_4 = i
print(largest_4)