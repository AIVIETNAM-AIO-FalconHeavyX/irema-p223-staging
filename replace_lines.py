import sys

with open("src/content/onboarding_catalog.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("output_lessons.txt", "r", encoding="utf-8") as f:
    new_lines = f.readlines()

# lines[143] is line 144 (0-indexed)
# lines[251] is line 252 (0-indexed)
# we want to replace lines 143 to 252 (inclusive) with new_lines
result = lines[:143] + new_lines + lines[252:]

with open("src/content/onboarding_catalog.py", "w", encoding="utf-8") as f:
    f.writelines(result)
