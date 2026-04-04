s = "mainteritumerachaddnajaavinvejoalladpunevichlaayiantodnibhavinve"

q = ["h", "a", "n", "s", "h", "a", "n", "s", "i", "n", "i", "w", "a", "a","g", "u", "c", "h", "a", "n", "n", "a"]

hash_map = {}
hash_list = [0] * 26

for ch in s:
    ascii_value = ord(ch)
    index = ascii_value -97
    hash_list[index] += 1
    print(hash_list)

for ch in q:
    ascii_value = ord(ch)
    index = ascii_value -97
    print(hash_list[index])






print("############# BETTER OPTIMIZED ############################")



print("########### CHARACTER HASHING USING ARRAY ###########################")

# Input string (source for frequency)
# Time: O(1) assignment | Space: O(n)

print("########### CHARACTER HASHING USING ARRAY ###########################")

# Input string (source for frequency)
# Time: O(1) assignment | Space: O(n)
s = "mainteritumerachaddnajaavinvejoalladpunevichlaayiantodnibhavinve"

# Query list (characters to check)
# Time: O(1) assignment | Space: O(m)
q = ["h", "a", "n", "s", "h", "a", "n", "s", "i", "n", "i", "w", "a", "a","g", "u", "c", "h", "a", "n", "n", "a"]

# Create hash array of size 26 (for a–z)
# index 0 -> 'a', index 25 -> 'z'
# Time: O(26) ~ O(1) | Space: O(26)
hash_list = [0] * 26


# ------------------ BUILD FREQUENCY FROM s ------------------
# Loop through each character in string s
# Time: O(len(s)) = O(n)
for ch in s:

    # Convert character to ASCII
    # Time: O(1)
    ascii_value = ord(ch)

    # Map 'a' → 0, 'b' → 1 ... 'z' → 25
    # Time: O(1)
    index = ascii_value - 97

    # Increment frequency
    # Time: O(1)
    hash_list[index] += 1


# ------------------ TRACK PRINTED CHARACTERS ------------------
# To avoid duplicate prints from q
# Time: O(26) ~ O(1) | Space: O(26)
visited = [0] * 26


# ------------------ PROCESS QUERY ------------------
# Loop through q
# Time: O(len(q)) = O(m)
for ch in q:

    ascii_value = ord(ch)       # O(1)
    index = ascii_value - 97    # O(1)

    # Check if character is lowercase a-z
    # Time: O(1)
    if 0 <= index < 26:

        # Print only once per character
        # Time: O(1)
        if visited[index] == 0:

            # Print character and its frequency
            # Time: O(1)
            print(f"{ch} -> {hash_list[index]}")

            # Mark as printed
            # Time: O(1)
            visited[index] = 1

    else:
        # If character is invalid (not a-z)
        print(f"{ch} -> 0")