package main

import (
	"cassandra-scanner/internal"
	"encoding/json"
	"flag"
	"io/ioutil"
	"log"
	"strings"
)

// Config matches the JSON structure passed from Python
type Config struct {
	InScope    []string `json:"in_scope_domains"`
	OutOfScope []string `json:"out_of_scope_domains"`
	OutputDir  string   `json:"output_dir"`
}

func main() {
	configFile := flag.String("config", "", "Path to config JSON")
	flag.Parse()

	if *configFile == "" {
		log.Fatal("Please provide --config [path]")
	}

	// 1. Load Config
	data, err := ioutil.ReadFile(*configFile)
	if err != nil {
		log.Fatalf("Failed to read config: %v", err)
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		log.Fatalf("Failed to parse config JSON: %v", err)
	}

	// 2. Run Subfinder
	log.Println("[+] Starting Recon Phase...")
	allSubs := internal.RunSubfinder(cfg.InScope)
	log.Printf("[+] Found %d raw subdomains.", len(allSubs))

	// 3. Filter Results
	var validSubs []string
	for _, sub := range allSubs {
		if internal.FilterDomains(sub, cfg.InScope, cfg.OutOfScope) {
			validSubs = append(validSubs, sub)
		}
	}
	log.Printf("[+] %d valid subdomains after filtering.", len(validSubs))

	// Save filtered subs
	err = ioutil.WriteFile(cfg.OutputDir+"/subdomains.txt", []byte(setupOutput(validSubs)), 0644)
	if err != nil {
		log.Printf("Failed to write subdomains: %v", err)
	}

	// 4. Run Httpx (Liveness Check)
	log.Println("[+] Starting Liveness Check with Httpx...")
	// We run httpx on 'validSubs' and it saves to 'alive.txt'
	// We then need to read alive.txt to pass to Nuclei? 
	// Or we just pass validSubs to Nuclei? User requirements said:
	// "Run httpx ... Save the alive.txt list."
	// "Update Python Logic: Ensure the Python attack modules only iterate through the domains listed in alive.txt"
	// "Run nuclei on valid domains." -> Usually implies ALIVE ones to save time.
	// Let's optimize: Pass ALIVE domains to Nuclei.
	
	aliveFile := internal.RunHttpx(validSubs, cfg.OutputDir)
	
	// Read alive domains
	var aliveSubs []string
	if aliveFile != "" {
		content, err := ioutil.ReadFile(aliveFile)
		if err == nil {
			// Parse lines
			lines := strings.Split(string(content), "\n")
			for _, l := range lines {
				l = strings.TrimSpace(l)
				if l != "" {
					// Httpx might return full URL (http://sub.com), we might need just domain for Nuclei?
					// Nuclei accepts URLs too.
					aliveSubs = append(aliveSubs, l)
				}
			}
		}
	}
	
	if len(aliveSubs) == 0 {
		log.Println("[-] No alive subdomains found. Skipping Nuclei.")
		return
	}
	log.Printf("[+] Found %d alive subdomains.", len(aliveSubs))

	// 5. Run Nuclei
	log.Println("[+] Starting Vulnerability Scan with Nuclei on alive targets...")
	internal.RunNuclei(aliveSubs, cfg.OutputDir)
}

func setupOutput(lines []string) string {
	var out string
	for _, l := range lines {
		out += l + "\n"
	}
	return out
}
