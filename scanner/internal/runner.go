package internal

import (
	"bufio"
	"bytes"
	"log"
	"os"
	"os/exec"
	"strings"
)

// RunSubfinder executes subfinder and returns a list of subdomains.
func RunSubfinder(domains []string) []string {
	log.Println("[*] Running Subfinder...")

	// 1. Sanitize and Prepare Input File
	// Create a temp file in current directory or temp
	f, err := os.CreateTemp("", "subfinder_targets_*.txt")
	if err != nil {
		log.Printf("Error creating temp file: %v", err)
		return []string{}
	}
	defer os.Remove(f.Name()) // Cleanup

	writer := bufio.NewWriter(f)
	for _, d := range domains {
		// Remove wildcard prefix if present
		clean := strings.TrimPrefix(d, "*.")
		writer.WriteString(clean + "\n")
	}
	writer.Flush()
	f.Close()

	// 2. Run Subfinder with -dL
	cmd := exec.Command("subfinder", "-dL", f.Name(), "-silent", "-t", "50", "-timeout", "10")
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Error running subfinder: %v. Output: %s", err, string(output))
		// Don't return empty immediately, some output might be there? 
		// Usually if err, output contains stderr.
		// If subfinder fails, we return what we have or empty.
		return []string{}
	}

	lines := strings.Split(string(output), "\n")
	var results []string
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed != "" {
			results = append(results, trimmed)
		}
	}
	return results
}

// RunHttpx filters for alive domains.
func RunHttpx(domains []string, outputDir string) string {
	log.Println("[*] Running Httpx for Liveness Check...")

	// Create temp file for domains
	f, err := os.CreateTemp("", "httpx_targets_*.txt")
	if err != nil {
		log.Printf("Error creating temp file: %v", err)
		return ""
	}
	defer os.Remove(f.Name())

	writer := bufio.NewWriter(f)
	for _, d := range domains {
		writer.WriteString(d + "\n")
	}
	writer.Flush()
	f.Close()

	outputFile := outputDir + "/alive.txt"
	// cmd: httpx -l targets.txt -o alive.txt -silent -mc 200,301,302,403,404
	cmd := exec.Command("httpx", "-l", f.Name(), "-o", outputFile, "-silent", "-mc", "200,301,302,403,404", "-timeout", "10")
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		// Log but don't fail hard, maybe no results
		log.Printf("Httpx finished with possible error: %v. Output: %s", err, string(output))
	} else {
		log.Println("[+] Httpx completed. Alive domains saved.")
	}
	
	return outputFile
}

// RunNuclei executes nuclei on a list of targets.
// Returns the path to the output file.
func RunNuclei(targets []string, outputDir string) string {
	log.Println("[*] Running Nuclei...")

	targetFile := outputDir + "/nuclei_targets.txt"
	f, err := os.Create(targetFile)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	writer := bufio.NewWriter(f)
	for _, t := range targets {
		writer.WriteString(t + "\n")
	}
	writer.Flush()

	outputFile := outputDir + "/nuclei_results.txt"
	
	// Nuclei Path Logic for Windows
	nucleiBin := "nuclei"
	path, err := exec.LookPath("nuclei")
	if err != nil {
		// Fallback for Windows
		homeDir, _ := os.UserHomeDir()
		fallback := homeDir + "\\go\\bin\\nuclei.exe"
		if _, err := os.Stat(fallback); err == nil {
			nucleiBin = fallback
			log.Printf("[*] Using Nuclei Fallback Path: %s", nucleiBin)
		} else {
			log.Println("[!] Nuclei executable not found in PATH or standard Go bin location.")
		}
	} else {
		log.Printf("[*] Found Nuclei at: %s", path)
	}

	cmd := exec.Command(nucleiBin, "-l", targetFile, "-o", outputFile, "-silent")
	
	// We might want to stream output or just wait.
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	
	err = cmd.Run()
	if err != nil {
		log.Printf("Error running nuclei: %v\nOutput: %s", err, out.String())
	} else {
		log.Println("[+] Nuclei scan completed.")
	}

	return outputFile
}
