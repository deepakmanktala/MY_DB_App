
################## THIS IS AN EXAMPLE OF HEAD RECURSION ##########################
################## JOB to be done followed by function call #############################


count = 0

def greeting():
    global count
    if count == 4:
        return
    print("Deepak ")
    count = count + 1
    greeting()

greeting()



############################ BELOW IS AN EXAMPLE OF TAIL ReCURSION --> FUNCTION CAll followed by JOB to be DONE ############################

counter = 0

def greeting_tail():

    global counter

    if counter == 4:
        return

    counter = counter + 1

    greeting_tail()

    print("My name is Deepak")

greeting_tail()