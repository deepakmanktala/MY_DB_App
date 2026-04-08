nums = [2,3,4,5,6,12,1,3,5,5,35]


############ Naive Approach ONLY PYTHON SPecific ##################
def right_rotate_by_1_in_place(nums):
    n = len(nums)
    # nums[:] = [nums[-1]] + nums[0:n-1]
    nums[:] = [nums[n-1]] + nums[:n-1]
    return nums

print(right_rotate_by_1_in_place(nums))


############ A little bit Optimal Approach ######################

nums2 = [3,4,45,5,6,6,4,43,43,43,43,43,43,43,2,3,4,5,6,7,8,9]
def right_rotate_by_1_in_place_optimal(nums2):
    n = len(nums2)
    print("len of the list nums2", len(nums2))
    temp = nums2[n-1]  ######### last element of the list is stored temporarily
    for i in range(n-2,-1,-1): ####### Reverse for loop starting form index n -2 , last element is n-1 and second last is n-2
        print("This is i ", i , " and now this is nums[i] and nums[i+1]", nums2[i],nums2[i+1])
        nums2[i+1] = nums2[i]
    nums2[0] = temp
    return nums2

print(right_rotate_by_1_in_place_optimal(nums2))