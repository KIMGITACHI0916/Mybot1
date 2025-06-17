package utils

import (
	"errors"
	"strconv"
	"strings"
	"time"
)

// ParseDuration converts a string like "5m", "2h" into time.Duration
func ParseDuration(input string) (time.Duration, error) {
	return time.ParseDuration(input)
}

// ParseSeconds parses "60", "2m", "1h" into seconds.
func ParseSeconds(input string) (int64, error) {
	if strings.HasSuffix(input, "s") ||
		strings.HasSuffix(input, "m") ||
		strings.HasSuffix(input, "h") {
		d, err := time.ParseDuration(input)
		if err != nil {
			return 0, err
		}
		return int64(d.Seconds()), nil
	}
	secs, err := strconv.Atoi(input)
	if err != nil {
		return 0, errors.New("invalid time format")
	}
	return int64(secs), nil
}