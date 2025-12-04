import sys
import os

# Add the parent directory of 'agent' to the path
sys.path.append(os.path.join(os.getcwd(), 'agents', 'oregon-state-scraper'))

from agent.agent import scrape_oregon_state_page

def test_scraper():
    url = "https://oregonstate.edu"
    print(f"Testing scraper with URL: {url}")
    result = scrape_oregon_state_page(url)
    
    if "Error" in result:
        print(f"FAILED: {result}")
        sys.exit(1)
    
    if "<html" in result.lower() or "<!doctype html" in result.lower():
        print("SUCCESS: Scraper returned HTML content.")
        print(f"Content length: {len(result)}")
    else:
        print("FAILED: Scraper did not return HTML content.")
        print(f"Result preview: {result[:100]}")
        sys.exit(1)

    # Test invalid URL
    invalid_url = "https://google.com"
    print(f"\nTesting scraper with invalid URL: {invalid_url}")
    result = scrape_oregon_state_page(invalid_url)
    if "Error: URL must be an oregonstate.edu domain" in result:
        print("SUCCESS: Scraper correctly rejected invalid URL.")
    else:
        print(f"FAILED: Scraper did not reject invalid URL. Result: {result}")
        sys.exit(1)

if __name__ == "__main__":
    test_scraper()
