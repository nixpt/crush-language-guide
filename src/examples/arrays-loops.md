# Arrays & Loops

Array creation, indexing, `for` iteration, `break`/`continue`, and a classic
loop exercise.

```crush
let arr = [10, 20, 30, 40, 50]
print("length: " + len(arr))
print("first: " + arr[0] + ", third: " + arr[2])

// iterate
let sum = 0
for x in arr {
    sum = sum + x
}
print("sum: " + sum)

// break — stop at 30
for x in arr {
    if x == 30 {
        break
    }
    print("before 30: " + x)
}

// continue — skip 30
for x in arr {
    if x == 30 {
        continue
    }
    print("not 30: " + x)
}

// build an array, index by position
let squares = []
for i in 1..6 {
    squares.push(i * i)
}
print(squares)

// strings index too
let s = "hello"
print(s[0] + s[4])

// fizzbuzz
for n in 1..16 {
    if n % 15 == 0 {
        print("FizzBuzz")
    } else if n % 3 == 0 {
        print("Fizz")
    } else if n % 5 == 0 {
        print("Buzz")
    } else {
        print(n)
    }
}
```

<!-- check: output -->
```text
length: 5
first: 10, third: 30
sum: 150
before 30: 10
before 30: 20
not 30: 10
not 30: 20
not 30: 40
not 30: 50
[1, 4, 9, 16, 25]
ho
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
```

**What this shows:**

- `[v1, v2, ...]` literals, `len(arr)`, zero-based `arr[i]`, and `arr.push(v)`
- `for x in arr` and half-open ranges `for i in 1..6` (1 through 5)
- `break` leaves the loop; `continue` skips to the next iteration
- Strings index like arrays, yielding one-character strings
- `if / else if / else` chains and `%`
