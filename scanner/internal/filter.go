package internal

import (
	"log"
	"strings"
)

// FilterDomains checks if a domain is allowed based on InScope and OutOfScope lists.
// It returns true if the domain is valid (in scope and NOT out of scope).
func FilterDomains(domain string, inScope []string, outOfScope []string) bool {
	// 1. Check if strictly out of scope
	for _, forbidden := range outOfScope {
		if Match(domain, forbidden) {
			log.Printf("[-] Dropped out-of-scope: %s (matched %s)", domain, forbidden)
			return false
		}
	}

	// 2. Check if in scope
	for _, allowed := range inScope {
		if Match(domain, allowed) {
			return true
		}
	}

	return false
}

// Match handles wildcards (e.g., *.example.com)
func Match(domain, pattern string) bool {
	if strings.Contains(pattern, "*") {
		// Simple wildcard matching
		suffix := strings.TrimPrefix(pattern, "*")
		return strings.HasSuffix(domain, suffix)
	}
	return domain == pattern
}
