nums = [1,2,3,4,5,5,56,67,54,54,67,6,654,5454,12]
k = 3

def rotate(self, nums: List[int], k: int) -> None:
    """
    # Do not return anything, modify nums in-place instead.
    # """

    # n = len(nums)
    # rotations = k%n

    # for _ in range(0,rotations): #########O(r)  ------ TC O(r*N)
    #     e = nums.pop()
    #     nums.insert(0,e) ##### O(N)

    ########### Using SLicing ########
    n = len(nums)
    r = k%n
    nums[:] = nums[n-r:] + nums[:n-r]



