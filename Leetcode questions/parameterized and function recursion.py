################### PARAMETRIZED RECURSION ########################

########### Time complexity O(N)#########################

############## Space Complexity O(N) - which is a Stack Space #######################################




### SUM of 1 to N Parameterized

def func(sum,i,N):
    if i > N:
        return
    sum = sum + i
    print(sum)

    func(sum, i+1, N)

func(0,1,10)





print("################### Final Code Corrceted ####################################")


def func_4(curr_sum, i, N):
    if i > N:
        return

    curr_sum = curr_sum + i      # O(1)
    print(curr_sum)              # O(1)

    func_4(curr_sum, i + 1, N)

func_4(0, 1, 10)



print("################### Final Code (With Deep Comments) ####################################")





# SUM of 1 to N (Parameterized Recursion)

def func_2(curr_sum, i, N):
    # Base condition: stop when i exceeds N
    if i > N:                         # O(1) time, O(1) space
        return                        # O(1)

    # Print current accumulated sum
    print(curr_sum)                   # O(1) time (ignoring I/O cost)

    # Recursive call:
    # - curr_sum + i → O(1)
    # - i + 1 → O(1)
    # - function call → adds new stack frame
    func_2(curr_sum + i, i + 1, N)      # O(1) work per call, stack grows


# Initial call
func_2(0, 1, 10)                       # O(1)



print ("####################### LAST Attempt AGAIN #########################")

def func_5(sum, i, N):
    if i > N:
        print(sum)
        return
    func_5(sum+i, i+1, N)

func_5(0, 1, 10)

