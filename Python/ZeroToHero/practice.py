def has_33(nums):
    counter = 0
    for num in nums:
        if (counter < len(nums) - 1):
            if num == 3 and nums[counter + 1] == 3:
                return True
            else:
                pass
            counter += 1
    return False

print(has_33([3, 1, 3]))