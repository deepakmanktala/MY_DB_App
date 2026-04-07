## Linked lists have value and next node pointers
## linked lists cn not be indexed


from typing import Optional


# ==============================
# Definition of a linked list node
# ==============================
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val          # value stored in this node
        self.next = next        # pointer to next node


# ==============================
# Solution class
# ==============================
class Solution:

    # ---------------------------------------------------
    # Iterative solution
    # Time Complexity: O(n + m)
    # Space Complexity: O(1)
    # ---------------------------------------------------
    def mergeTwoLists_iterative(
            self,
            list1: Optional[ListNode],
            list2: Optional[ListNode]
    ) -> Optional[ListNode]:

        # Create a dummy node to simplify merging
        dummy = ListNode(-1)

        # 'current' will always point to the last node
        # in the merged linked list
        current = dummy

        # Traverse both lists until one becomes empty
        while list1 is not None and list2 is not None:

            # Compare current node values
            if list1.val <= list2.val:
                current.next = list1       # attach list1 node
                list1 = list1.next         # move list1 forward
            else:
                current.next = list2       # attach list2 node
                list2 = list2.next         # move list2 forward

            # Move merged-list pointer forward
            current = current.next

        # Attach the remaining part of whichever list is left
        if list1 is not None:
            current.next = list1
        else:
            current.next = list2

        # Return the real head (skip dummy)
        return dummy.next

    # ---------------------------------------------------
    # Recursive solution
    # Time Complexity: O(n + m)
    # Space Complexity: O(n + m) because of recursion stack
    # ---------------------------------------------------
    def mergeTwoLists_recursive(
            self,
            list1: Optional[ListNode],
            list2: Optional[ListNode]
    ) -> Optional[ListNode]:

        # Base case: if list1 is empty, return list2
        if list1 is None:
            return list2

        # Base case: if list2 is empty, return list1
        if list2 is None:
            return list1

        # Choose the smaller node and recursively merge the rest
        if list1.val <= list2.val:
            list1.next = self.mergeTwoLists_recursive(list1.next, list2)
            return list1
        else:
            list2.next = self.mergeTwoLists_recursive(list1, list2.next)
            return list2


# ==============================
# Helper function:
# Convert Python list -> Linked List
# Example: [1,2,4] -> 1 -> 2 -> 4
# ==============================
def build_linked_list(values):
    # If list is empty, linked list is None
    if not values:
        return None

    # Create the head node from first value
    head = ListNode(values[0])

    # 'current' will be used to build the chain
    current = head

    # Create remaining nodes
    for i in range(1, len(values)):
        current.next = ListNode(values[i])   # create new node and link it
        current = current.next               # move forward

    return head


# ==============================
# Helper function:
# Convert Linked List -> Python list
# Useful for easy checking/debugging
# ==============================
def linked_list_to_list(head):
    result = []

    current = head
    while current is not None:
        result.append(current.val)
        current = current.next

    return result


# ==============================
# Helper function:
# Print linked list nicely
# ==============================
def print_linked_list(head):
    if head is None:
        print("None")
        return

    current = head
    while current is not None:
        print(current.val, end="")
        if current.next is not None:
            print(" -> ", end="")
        current = current.next

    print(" -> None")


# ==============================
# Main testing block
# This runs when you click Run in IntelliJ
# ==============================
if __name__ == "__main__":

    # Create object of Solution class
    sol = Solution()

    # ----------------------------------
    # Test Case 1
    # ----------------------------------
    print("TEST CASE 1")
    list1 = build_linked_list([1, 2, 4])
    list2 = build_linked_list([1, 3, 4])

    print("Input list1:")
    print_linked_list(list1)

    print("Input list2:")
    print_linked_list(list2)

    merged_iterative = sol.mergeTwoLists_iterative(list1, list2)

    print("Merged list using ITERATIVE solution:")
    print_linked_list(merged_iterative)
    print("As Python list:", linked_list_to_list(merged_iterative))
    print()

    # ----------------------------------
    # Rebuild lists because the first merge
    # reuses and modifies the original nodes
    # ----------------------------------
    list1 = build_linked_list([1, 2, 4])
    list2 = build_linked_list([1, 3, 4])

    merged_recursive = sol.mergeTwoLists_recursive(list1, list2)

    print("Merged list using RECURSIVE solution:")
    print_linked_list(merged_recursive)
    print("As Python list:", linked_list_to_list(merged_recursive))
    print()

    # ----------------------------------
    # Test Case 2
    # ----------------------------------
    print("TEST CASE 2")
    list1 = build_linked_list([])
    list2 = build_linked_list([])

    print("Input list1:")
    print_linked_list(list1)

    print("Input list2:")
    print_linked_list(list2)

    merged = sol.mergeTwoLists_iterative(list1, list2)

    print("Merged list:")
    print_linked_list(merged)
    print("As Python list:", linked_list_to_list(merged))
    print()

    # ----------------------------------
    # Test Case 3
    # ----------------------------------
    print("TEST CASE 3")
    list1 = build_linked_list([])
    list2 = build_linked_list([0])

    print("Input list1:")
    print_linked_list(list1)

    print("Input list2:")
    print_linked_list(list2)

    merged = sol.mergeTwoLists_iterative(list1, list2)

    print("Merged list:")
    print_linked_list(merged)
    print("As Python list:", linked_list_to_list(merged))
    print()

    # ----------------------------------
    # Test Case 4
    # ----------------------------------
    print("TEST CASE 4")
    list1 = build_linked_list([1, 1, 2, 5])
    list2 = build_linked_list([1, 3, 4, 10])

    print("Input list1:")
    print_linked_list(list1)

    print("Input list2:")
    print_linked_list(list2)

    merged = sol.mergeTwoLists_iterative(list1, list2)

    print("Merged list:")
    print_linked_list(merged)
    print("As Python list:", linked_list_to_list(merged))