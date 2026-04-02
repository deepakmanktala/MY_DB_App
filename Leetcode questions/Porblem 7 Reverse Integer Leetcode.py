class Solution:
    def reverse(self, x: int) -> int:
        # 32-bit signed integer upper and lower limits
        INT_MIN = -2**31
        INT_MAX = 2**31 - 1

        # Store sign separately
        sign = -1 if x < 0 else 1

        # Work only with positive number to avoid Python negative % and // quirks
        x = abs(x)

        # This will hold the reversed number
        rev = 0

        # Process digits one by one
        while x != 0:
            # Take the last digit
            pop = x % 10

            # Remove the last digit from x
            x //= 10

            # Check if rev * 10 + pop would overflow INT_MAX
            if rev > INT_MAX // 10 or (rev == INT_MAX // 10 and pop > 7):
                return 0

            # Append digit to reversed number
            rev = rev * 10 + pop

        # Reapply original sign
        rev *= sign

        # Final safety check for full 32-bit signed range
        if rev < INT_MIN or rev > INT_MAX:
            return 0

        return rev


if __name__ == "__main__":
    obj = Solution()

    # Test inputs
    test_cases = [123, -123, 120, -1563847412]

    for x in test_cases:
        result = obj.reverse(x)
        print(f"Input: {x} → Output: {result}")