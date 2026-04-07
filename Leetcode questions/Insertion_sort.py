##########Insertion SOrt - NOT COMPLETE YET



nums = [3,4,5,6,71,2,3,9,7,12,132,12,156,1,3,4,5,68,9]

n = len(nums)

for i in range(n):
    key = nums[i]
    j = i-1
    while j >= 0 and key < nums[j]:
        nums[j+1] = key
