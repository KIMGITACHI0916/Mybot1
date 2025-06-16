
package main

import (
  "time"
  "sync"
)

type FloodGuard struct {
  mu sync.Mutex
  userTimes map[int64]map[int64]time.Time
}

func NewFloodGuard() *FloodGuard {
  return &FloodGuard{userTimes: make(map[int64]map[int64]time.Time)}
}

func (f *FloodGuard) Process(chatID, userID int64) {
  f.mu.Lock(); defer f.mu.Unlock()
  if _, ok := f.userTimes[chatID]; !ok {
    f.userTimes[chatID] = make(map[int64]time.Time)
  }
  f.userTimes[chatID][userID] = time.Now()
}

func (f *FloodGuard) IsFlood(chatID, userID int64) bool {
  f.mu.Lock(); defer f.mu.Unlock()
  last, ok := f.userTimes[chatID][userID]
  if !ok { return false }
  return time.Since(last) < time.Second
}
