import sys

with open("app/platforms/flipkart.py", "r") as f:
    lines = f.readlines()

# Indent lines 307 to 386
for i in range(306, 386):
    if lines[i].strip(): # Only indent if not empty
        lines[i] = "    " + lines[i]

with open("app/platforms/flipkart.py", "w") as f:
    f.writelines(lines)
