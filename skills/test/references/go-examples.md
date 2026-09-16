# Go Test Examples

Comprehensive Go testing patterns using table-driven tests and the standard testing package.

---

## Table-Driven Test Structure

```go
package module

import (
    "testing"
)

func TestFunctionName(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
        wantErr  bool
    }{
        {"normal input", "valid", "expected", false},
        {"empty input", "", "default", false},
        {"boundary value", "MAX", "boundary", false},
        {"invalid input", "bad", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := FunctionName(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("FunctionName() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.expected {
                t.Errorf("FunctionName() = %v, want %v", got, tt.expected)
            }
        })
    }
}
```

## Running Tests

```bash
# Run all tests
go test ./...

# With coverage
go test -cover ./...

# Verbose
go test -v ./...

# Specific package
go test ./pkg/module
```

## Coverage Analysis

```bash
go test -cover ./...
```

## Detect Project Type

```bash
ls *_test.go 2>/dev/null
```
