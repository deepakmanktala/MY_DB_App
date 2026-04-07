


###################    Selection Sort Practice , Ascending Order####################################
nums = [3,5,9,8,7,6,5,43,21,1,4,6]

def selection_sort(nums):
    for i in range(len(nums)):
        min_index = i
        for j in range(i+1,len(nums)):
            if nums[j] < nums[min_index]:
                min_index = j
                nums[min_index], nums[i] = nums[i], nums[min_index]
    return nums

print(selection_sort(nums))


###################    Selection Sort Practice , Descending Order  #########################################

nums2 = [4,5,6,7,1,2,3,4,5,9,8,7,6,5,4,121,545,232,54]
def selection_sort_descending(nums):
    for i in range(len(nums)):
        max_index = len(nums)-1
        for j in range(i+1,len(nums)):
            if nums[j]>nums[i]:
                max_index = j
                nums[i], nums[j] = nums[j], nums[i]

    return nums

print(selection_sort_descending(nums2))
# # x =-1
# #
# # y = x % 10
# #
# # print (y, 'this is what y is')
# #
# # z = x// 10
# #
# # print(z, 'this is what z is')
# #
# #
# # print(2**0)
# # #
#
#
# print("#######################Binary conversions ################")
#
#
# def reverseBits(n):
#     rev_bit = 0
#
#     for i in range(32):
#         bit = (n >> i) & 1
#         print("Only BIT operation ", bit, rev_bit)
#         rev_bit = rev_bit | (bit << (31 - i))
#         print("rev_bit operation here", bit, rev_bit)
#     return rev_bit
#
#
# print(reverseBits(3232345))
# print(reverseBits(411212233))
# # n = 100
# # binary = ""
# #
# # if n == 0:
# #     binary = "0"
# # else:
# #     while n > 0:
# #         remainder = n % 2       # Get the remainder (0 or 1)
# #         print(remainder)
# #         binary = str(remainder) + binary  # Prepend remainder to the string
# #         print(binary)
# #         n = n // 2              # Perform integer division by 2
# #
# # print(binary)  # Output: 111
# #
# #
# #
# #
# # print("#######################Binary conversions using recursion ################")
# #
# #
# #
# # def decimal_to_binary(num):
# #     if num > 1:
# #         decimal_to_binary(num // 2)
# #     print(num % 2, end='')
# #
# # decimal_to_binary(7)  # Output: 111
# # print(" Now next number" )
# # decimal_to_binary(100)  # Output: 1111100100



def fibonacci(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)

print(fibonacci(9))
