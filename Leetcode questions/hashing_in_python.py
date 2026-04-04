
############# READ In DEPTh AGAIN And Practice Hard ################

############# READ In DEPTh AGAIN And Practice Hard ################


############# READ In DEPTh AGAIN And Practice Hard ################


## Hashing in Python is a pre-storing of values wither in Dict, List or Set - and it is called hashing

n = [1,2,3,4,5,5,6,6,7,7,8,8]
m = [122,34,45,56,667,77,77,1,1,1,1,2,2,2,3,3,3,4,5,6,7,8]


''' Constraints 1 <= n[i] <= 10 
    n can have max 10^8 elements
    m can have max 10^8 elements
    n should be b/w 1 to 10, m can have  as many values'''




print("########## Brute Force ###############")


##### Time complexity is O(m*n), 10^8 * 10^8  --> 10 ^16 - so it needs to be optimized
##### Space complexity O(1)

for num in m:
    count = 0
    for i in n:
        if i == num:
            count += 1
    print(num, count)


############# HASH LIST Optimization ####################
print("###########################Hashing Mechanism in Python #######################################")
#
#
# n = [1,2,3,4,5,5,6,6,7,7,8,8]
# m = [122,34,45,56,667,77,77,1,1,1,1,2,2,2,3,3,3,4,5,6,7,8]
# hash_list = [0] * len(n)
#
# for i in range(len(n)):
#     hash_list[i] += 1
#
# for i in m:
#     if i < 1 or i > 10:
#         print(0)
#     else:
#         print(hash_list[i])

#
# print("### Element -> Frequency ###")
# # Just printing a header for clarity in output
#
#
# # Input list whose frequency we want to store
# n = [1,2,3,4,5,5,6,6,7,7,8,8]
#
# # Query list → we will check frequency of each element in this list
# m = [122,34,45,56,667,77,77,1,1,1,1,2,2,2,3,3,3,4,5,6,7,8]
#
#
# # Step 1: Find maximum value in n
# # This is required because array hashing needs a fixed size
# # We must ensure all values in n can be used as indices
# max_val = max(n)
#
#
# # Step 2: Create hash array (frequency array)
# # Size = max_val + 1 because indexing starts from 0
# # Example: if max_val = 8 → array size = 9 (index 0 to 8)
# hash_list = [0] * (max_val + 1)
#
#
# # Step 3: Store frequency of each element in n
# # Loop through each value in n
# for i in n:
#     # Use the value itself as index and increment count
#     # Example: if i = 5 → hash_list[5] += 1
#     hash_list[i] += 1
#
#
# # At this point, hash_list looks like:
# # index:      0 1 2 3 4 5 6 7 8
# # frequency:  0 1 1 1 1 2 2 2 2
#
#
# # Step 4: Query frequencies for each element in m
# for i in m:
#
#     # Condition to handle out-of-bound values
#     # If i is negative OR greater than max_val, it doesn't exist in hash
#     if i < 0 or i > max_val:
#         print(f"{i} -> 0")   # Print 0 frequency
#
#     else:
#         # If valid index → print frequency from hash_list
#         print(f"{i} -> {hash_list[i]}")



print("########################### Hashing Mechanism in Python #######################################")

# n is the source list from which frequency/hash is built
n = [1, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8]

# m is the query list containing all possible values to check
m = [122, 34, 45, 56, 667, 77, 77, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, -1]

# Define allowed range for values that can exist in n
min_val = 1
max_val = 10

# Create frequency array for values from 0 to 10
# Index = number, value at that index = count/frequency
hash_list = [0] * (max_val + 1)

# Fill frequency array using values from n
for value in n:
    # Only count numbers that are inside valid range
    if min_val <= value <= max_val:
        hash_list[value] += 1

# visited_valid keeps track of which valid numbers from m were already printed
visited_valid_hash = [0] * (max_val + 1)

# printed_invalid stores invalid values already printed,
# so repeated invalid values are aggregated too
printed_invalid = []

# Process each query from m
for value in m:

    # If value cannot exist in n, print 0 only once
    if value < min_val or value > max_val:
        if value not in printed_invalid:
            print(f"{value} -> 0")
            printed_invalid.append(value)

    # If value is valid, print its frequency from n only once
    else:
        if visited_valid_hash[value] == 0:
            print(f"{value} -> {hash_list[value]}")
            visited_valid_hash[value] = 1


print("########### WRITE IT USING DICTIONARY NOW ###########################")

#
# # n is the source list from which frequency/hash is built
# n = [1, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8]
#
# # m is the query list containing all possible values to check
# m = [122, 34, 45, 56, 667, 77, 77, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, -1]
#
# min_val = 1
# max_val = 10
# hash_list = [0] * (max_val + 1)
#
# freq_dict = {}
# for value in m:
#     if min_val <= value <= max_val:
#         if value not in freq_dict:
#             freq_dict[value] = 1
#         else:
#             freq_dict[value] += 1
#     else:
#         if visited_valid_hash[value] == 0:

















# ########### WRITE IT USING DICTIONARY NOW ###########################
# Time Complexity  : O(1)
# Space Complexity : O(1)
# Reason           : Printing a fixed string is constant-time in algorithm discussion
#                    (strictly speaking, print depends on output size, but this is tiny/fixed).
print("########### WRITE IT USING DICTIONARY NOW ###########################")


# Source list from which frequency/hash is built.
# We will PRECOMPUTE frequencies from this list.
# Time Complexity  : O(1) for assignment of reference to the list object
# Space Complexity : O(n) because list n stores n elements
n = [1, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8]


# Query list containing all possible values to check.
# We will use this list only for lookup/printing.
# Time Complexity  : O(1) for assignment of reference
# Space Complexity : O(m) because list m stores m elements
m = [122, 34, 45, 56, 667, 77, 77, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, -1]


# Define minimum valid value allowed in n.
# Any query value smaller than this is treated as invalid and should print 0.
# Time Complexity  : O(1)
# Space Complexity : O(1)
min_val = 1


# Define maximum valid value allowed in n.
# Any query value larger than this is treated as invalid and should print 0.
# Time Complexity  : O(1)
# Space Complexity : O(1)
max_val = 10


# Dictionary to store frequency of values from n.
# Key   = number from n
# Value = how many times that number appears in n
#
# Example after building:
# {
#   1: 1,
#   2: 1,
#   3: 1,
#   4: 1,
#   5: 2,
#   6: 2,
#   7: 2,
#   8: 2
# }
#
# Time Complexity  : O(1) to create empty dictionary
# Space Complexity : O(1) initially, grows later up to O(u)
#                    where u = number of unique valid elements in n
hash_dict = {}


# ---------------------- BUILD FREQUENCY HASH FROM n ----------------------
# We traverse each element of n exactly once.
#
# Loop Time Complexity  : O(len(n)) = O(n)
# Extra Space Complexity: O(u), where u = unique valid values stored in hash_dict
for value in n:

    # Check whether current value is inside the allowed valid range.
    # This prevents invalid values from being stored in hash_dict.
    #
    # Time Complexity  : O(1)
    # Space Complexity : O(1)
    if min_val <= value <= max_val:

        # If value is not already in hash_dict, this is the first occurrence.
        # We create a new key with frequency 1.
        #
        # Dictionary membership check average case:
        # Time Complexity  : O(1)
        # Space Complexity : O(1)
        if value not in hash_dict:

            # Insert the key for the first time.
            #
            # Time Complexity  : O(1) average
            # Space Complexity : O(1) extra for this operation
            #                    (overall dictionary may grow to O(u))
            hash_dict[value] = 1

        else:
            # If the key already exists, increment its frequency count.
            #
            # Example:
            # hash_dict[5] was 1, now becomes 2
            #
            # Time Complexity  : O(1) average
            # Space Complexity : O(1)
            hash_dict[value] += 1


# Dictionary to track which query values from m have already been printed.
# This ensures aggregation:
# if 1 appears many times in m, we print it only once.
#
# Example:
# m = [1, 1, 1, 2, 2]
# printed becomes:
# {
#   1: 1,
#   2: 1
# }
#
# Time Complexity  : O(1) to create empty dictionary
# Space Complexity : O(1) initially, grows later to O(v)
#                    where v = number of unique elements in m
printed = {}


# ---------------------- PROCESS QUERY LIST m ----------------------
# We traverse each element of m exactly once.
#
# Loop Time Complexity  : O(len(m)) = O(m)
# Extra Space Complexity: O(v), where v = number of unique query elements stored in printed
for value in m:

    # We only want to print each unique query value once.
    # So first check whether this value was already processed/printed.
    #
    # Example:
    # if value = 1 and printed already contains 1,
    # then skip printing duplicate output.
    #
    # Time Complexity  : O(1) average
    # Space Complexity : O(1)
    if value not in printed:

        # If current query value is inside valid allowed range,
        # it is eligible to exist in n.
        #
        # Time Complexity  : O(1)
        # Space Complexity : O(1)
        if min_val <= value <= max_val:

            # Print the frequency of this valid value from hash_dict.
            #
            # hash_dict.get(value, 0) means:
            # - if value exists in hash_dict, return its frequency
            # - otherwise return 0
            #
            # This handles cases like:
            # value is valid (e.g. 9 or 10), but 9/10 may not actually be present in n
            # so output should still be 0.
            #
            # Example:
            # value = 5  -> hash_dict.get(5, 0) returns 2
            # value = 9  -> hash_dict.get(9, 0) returns 0
            #
            # Time Complexity  : O(1) average for dictionary lookup
            # Space Complexity : O(1)
            print(f"{value} -> {hash_dict.get(value, 0)}")

        else:
            # If query value is outside the allowed range,
            # then by definition it cannot exist in n.
            # So print 0.
            #
            # Example:
            # value = 122 -> invalid -> print 0
            # value = -1  -> invalid -> print 0
            #
            # Time Complexity  : O(1)
            # Space Complexity : O(1)
            print(f"{value} -> 0")

        # Mark this query value as already printed.
        # This avoids duplicate printing for repeated values in m.
        #
        # Example:
        # first time value = 1 -> printed[1] = 1
        # next time value = 1 -> skipped because 1 is already in printed
        #
        # Time Complexity  : O(1) average
        # Space Complexity : O(1) extra for this operation
        #                    (overall printed dictionary may grow to O(v))
        printed[value] = 1


# ---------------------- OVERALL COMPLEXITY SUMMARY ----------------------
#
# 1. Building hash_dict from n:
#    Time Complexity  : O(n)
#    Space Complexity : O(u)
#    where u = number of unique valid elements in n
#
# 2. Processing m and printing each unique query once:
#    Time Complexity  : O(m)
#    Space Complexity : O(v)
#    where v = number of unique elements in m
#
# 3. Overall program:
#    Time Complexity  : O(n + m)
#    Space Complexity : O(u + v)
#
# In worst case:
#    u can be up to n
#    v can be up to m
# so worst-case space can be written as:
#    O(n + m)
#
#
# ---------------------- IMPORTANT CONCEPTUAL SUMMARY ----------------------
#
# hash_dict:
#   stores frequencies PRECOMPUTED from n
#
# printed:
#   stores which values from m have already been output
#
# So this program does TWO jobs:
#   1. build frequency hash from n
#   2. aggregate duplicate queries from m and print each query only once
#
#
# ---------------------- SAMPLE OUTPUT FOR CURRENT INPUT ----------------------
#
# 122 -> 0
# 34 -> 0
# 45 -> 0
# 56 -> 0
# 667 -> 0
# 77 -> 0
# 1 -> 1
# 2 -> 1
# 3 -> 1
# 4 -> 1
# 5 -> 2
# 6 -> 2
# 7 -> 2
# 8 -> 2
# -1 -> 0
#
#
# ---------------------- WHY DICTIONARY VERSION IS GOOD ----------------------
#
# Advantages:
#   - No need to create a huge array if values are large
#   - Handles sparse values efficiently
#   - Average O(1) lookup and insert
#
# Compare with array hashing:
#   - array hashing is great when value range is small and fixed
#   - dictionary hashing is better when values can be large, sparse, or unknown






















print("########### WRITE IT USING DICTIONARY NOW ###########################")  # O(1) time, O(1) space

n = [1, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8]  # O(1) assignment, list storage O(n)
m = [122, 34, 45, 56, 667, 77, 77, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, -1]  # O(1) assignment, list storage O(m)

min_val = 1   # O(1) time, O(1) space
max_val = 10  # O(1) time, O(1) space

hash_dict = {}  # O(1) time, O(1) initial space

# Build frequency map from n
# Total loop complexity: O(n) time
for value in n:
    if min_val <= value <= max_val:  # O(1) time, O(1) space
        if value not in hash_dict:   # O(1) average time, O(1) space
            hash_dict[value] = 1     # O(1) average time, O(1) space
        else:
            hash_dict[value] += 1    # O(1) average time, O(1) space

printed = {}  # O(1) time, O(1) initial space

# Process query list m
# Total loop complexity: O(m) time
for value in m:
    if value not in printed:  # O(1) average time, O(1) space

        if min_val <= value <= max_val:  # O(1) time, O(1) space
            print(f"{value} -> {hash_dict.get(value, 0)}")  # O(1) avg lookup, O(1) extra space
        else:
            print(f"{value} -> 0")  # O(1) time, O(1) space

        printed[value] = 1  # O(1) average time, O(1) space


# Overall Program Complexity:
# Time  = O(n + m)
# Space = O(u + v)
# where:
#   u = number of unique valid elements in n
#   v = number of unique elements in m
#
# Worst-case:
# Time  = O(n + m)
# Space = O(n + m)