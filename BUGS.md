# Kofty — Known Bugs and Gaps

Discovered 2026-10-15 while building `examples/showcase.kfy`.
Seven distinct issues, ordered by severity. See `ARCHITECTURE.md`
for why these weren't caught by the existing test suite.

Each entry has: symptom, minimal reproduction, root cause,
impact, priority, and a fix sketch. Fixes are serial — one per
batch, verified in isolation — because this session's experience
showed that combined fixes hide interactions.

---

## #1 — Container `is_to_string` overloads are declared after the
## templates that use them (two-phase lookup failure)

**Symptom.**
```python
xs = [(1, 2), (3, 4)]
print(xs)

no matching function for call to
  'is_to_string(const std::pair<int, int>&)'
candidates: is_to_string(string), is_to_string(char*),
            is_to_string(int), is_to_string(double), is_to_string(bool)

ys = [1, 2]
zs = [3, 4]
print(ys + zs)                 # list concat
print(xs[1:4])                 # slice
s1 = {1, 2, 3}
s2 = {3, 4, 5}
print(s1 | s2)                 # set union

counter = 0
while counter < 3:
    ...
    counter = counter + 1

for counter in range(10):
    ...

def sum_all(*nums):
    ...
print(sum_all(1, 2, 3))

could not convert '1' from 'int' to 'std::vector<int>'

d = {"a": 1}
...
d = SomeClass("x")     # reassign to a different type

def safe_pop(xs, i):
    return xs.pop(i)

class Account:
    def __init__(self, owner, balance):
        ...
acct = Account("Alice", 100)

invalid conversion from 'const char*' to 'int'
