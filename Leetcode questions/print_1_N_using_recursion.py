
def func(x,N):

    if x>=N+1:
        return
    print(x)
    func(x+1, N)

func(1,20)


def func_second(N):
    # if N==0:
    #     return
    # x = 1
    # print(x)
    # x += 1
    # func_second(N-1)

    if N==0:
        return
    func_second(N-1)
    print(N)



func_second(20)



#
#
#     func_second(5)
# calls func_second(4)
# calls func_second(3)
# calls func_second(2)
# calls func_second(1)
# calls func_second(0)
# returns
# print(1)
# returns
# print(2)
# returns
# print(3)
# returns
# print(4)
# returns
# print(5)
# returns
#
#
# Simple analogy
#
# Imagine going down stairs to the basement:
#
# floor 5
# floor 4
# floor 3
# floor 2
# floor 1
# floor 0
#
# You do nothing while going down.
#
# Once you hit floor 0, you come back up and announce each floor:
#
# 1
# 2
# 3
# 4
# 5
#
# That is exactly what your recursion is doing.


#
# func(20)
# ↓
# func(19)
# ↓
# func(18)
# ↓
# ...
# ↓
# func(3)
# ↓
# func(2)
# ↓
# func(1)
# ↓
# func(0)  ← base case hit


######## STACK ################

# TOP
# func(0)
# func(1)
# func(2)
# func(3)
# ...
# func(18)
# func(19)
# func(20)
# BOTTOM



######################################

# GOING DOWN (NO PRINT)
# ---------------------
# 20 → 19 → 18 → ... → 2 → 1 → 0
#
# COMING UP (PRINT HAPPENS)
# -------------------------
# 0 → 1 → 2 → 3 → ... → 19 → 20
# ↑   ↑   ↑
# print print print








#
#
# 🪜 Ladder Analogy
#
# You go down a ladder:
#
# Step 20
# Step 19
# Step 18
# ...
# Step 1
# Step 0 (bottom)
#
# 👉 You say nothing while going down
#
# Now you climb back up:
#
# Step 1 → say "1"
# Step 2 → say "2"
# ...
# Step 20 → say "20"


############## HEAD RECURSION ############
def func_third(i, N):
    if i > N:
        return

    print(i)
    func_third(i+1, N)

func_third(1,20)



########## TAIl RECURSION - BACK TRACKING
def func_third(i, N):
    if i > N:
        return


    func_third(i+1, N)
    print(i)

func_third(1,20)


##########################################################################
########################################################################################
print ("###########################its a function four now- func_four ##################")
def func_four(N):
    if N==0:
        return


    func_four(N-1)
    print(N)

func_four(20)
