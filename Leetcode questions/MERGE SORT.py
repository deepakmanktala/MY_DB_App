def merge_two_Sorted_ararys_or_lists(nums1,nums2):
    sorted_list = []
    len_nums1 = len(nums1)
    len_nums2 = len(nums2)

    i = j = 0

    while i < len_nums1 and j < len_nums2:
        if nums1[i] < nums2[j]:
            sorted_list.append(nums1[i])
            i += 1
        else:
            sorted_list.append(nums2[j])
            j += 1

    # Step 2: Add remaining elements from nums1 (if any)
    while i < len_nums1:
        sorted_list.append(nums1[i])
        i += 1

    # Step 3: Add remaining elements from nums2 (if any)
    while j < len_nums2:
        sorted_list.append(nums2[j])
        j += 1
    return sorted_list


nums1 = [1,2,3,4,5,6,70,80, 90,100]
nums2 = [12,13,14,15,16,17,18,19]

print(merge_two_Sorted_ararys_or_lists(nums1,nums2))