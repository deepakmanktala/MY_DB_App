nums = [12,2,2,2,1,1,1,1,1,13,3,4,5,6,7,8,9,9,66,4,4,4,4,4,6,7,7,89,9,9,9,95,4,34,43,4,3,4,34,3,4,34,34]

######### Space complexity in the worst case would be O(N) as it would 1;1, 2:1, 3:1, otherwise it can be O(k) where k < N
########## dict append , dict access is O(N) time complexity

dict = {}

# freq_map1 = dict()
freq_map = {}

for i in range(0,len(nums)):          ####TC O(n)
    if nums[i] in freq_map:           ####TC O(1)
        freq_map[nums[i]] += 1
    else:
        freq_map[nums[i]] = 1          ####TC O(1)

x = 1

print(freq_map[x])  ####TC O(1)

# freq_map.keys(
print(freq_map)

#
# for num in num:
#     if num not in dict:
#         dict[num] = 1
#     else:



#####################Method 2############################

print("######################## Method 2 ###########################")

nums_2 =[1,1,1,1,2,2,2,2,3,3,4,45,5,5,7,7,8,8,8,9,9,9,95,5]

dict2_hash_map = {}

n = len(nums_2)#### O(N)
for i in range(0,n):
    dict2_hash_map[nums_2[i]] = dict2_hash_map.get(nums_2[i], 0) + 1 ##O(2)

print(dict2_hash_map)


########## READ MORE ABOUT HASHMAPS