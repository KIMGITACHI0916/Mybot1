package models

import "sync"

// AFKUser stores AFK status for a user.
type AFKUser struct {
	UserID    int
	Reason    string
	Timestamp int64
}

var (
	afkUsers = make(map[int]*AFKUser)
	mu       sync.Mutex
)

// SetAFK marks a user as AFK.
func SetAFK(userID int, reason string, timestamp int64) {
	mu.Lock()
	defer mu.Unlock()
	afkUsers[userID] = &AFKUser{
		UserID:    userID,
		Reason:    reason,
		Timestamp: timestamp,
	}
}

// RemoveAFK removes AFK status for a user.
func RemoveAFK(userID int) {
	mu.Lock()
	defer mu.Unlock()
	delete(afkUsers, userID)
}

// IsAFK checks if a user is AFK.
func IsAFK(userID int) (*AFKUser, bool) {
	mu.Lock()
	defer mu.Unlock()
	afk, ok := afkUsers[userID]
	return afk, ok
}