```markdown
# VECTIS Error Message Guidelines

## Introduction

This document outlines the guidelines for creating and maintaining error messages in the VECTIS language. Error messages are critical for user experience and should be clear, concise, and accessible. This document ensures that all error messages adhere to a consistent format and provide actionable guidance to users.

## Error Message Structure

An error message should include the following components:

1. **Code**: A unique code that identifies the type of error.
2. **Severity**: The severity level of the error (e.g., error, warning).
3. **Message**: A human-readable message that explains the error.
4. **Source Span**: Information about the location of the error in the source code.

## Error Message Format

Error messages should be formatted in a consistent manner to ensure clarity and consistency across the VECTIS language. The format should be:

```
[Code] [Severity]: [Message] [Source Span]
```

### Example

```
LEX001 error: Unterminated string literal at file:line:column
```

## Error Message Guidelines

1. **Code**: Use a unique code for each type of error. The code should be a combination of the error type and a sequential number.
2. **Severity**: Use the appropriate severity level for each error. Errors that prevent the program from continuing should be marked as `error`, while warnings should be marked as `warning`.
3. **Message**: The message should be clear and concise. It should explain the error and provide actionable guidance to the user.
4. **Source Span**: Include the source span information to help the user locate the error in their source code.

## Error Message Examples

### Example 1: Unterminated String Literal

```
LEX001 error: Unterminated string literal at file:1:10
```

### Example 2: Unsupported Bare Operator

```
LEX002 error: Unsupported bare operator at file:2:5
```

### Example 3: Unrecognized Character

```
LEX003 error: Unrecognized character at file:3:3
```

### Example 4: Expected Statement

```
SYN001 error: Expected statement at file:4:1
```

### Example 5: Standalone Otherwise

```
SYN002 error: Standalone otherwise at file:5:1
```

### Example 6: Expected Required Token

```
SYN003 error: Expected required token at file:6:10
```

### Example 7: Expected Expression

```
SYN004 error: Expected expression at file:7:5
```

### Example 8: Unclosed Block

```
SYN005 error: Unclosed block at file:8:1
```

### Example 9: Malformed Citation Collection

```
SYN006 error: Malformed citation collection at file:9:1
```

### Example 10: Reserved Keyword Cannot Begin a Statement

```
SYN007 error: Reserved keyword cannot begin a statement at file:10:1
```

## Conclusion

This document outlines the guidelines for creating and maintaining error messages in the VECTIS language. By following these guidelines, we can ensure that all error messages are clear, concise, and accessible, improving the user experience and reducing the likelihood of errors.
```
