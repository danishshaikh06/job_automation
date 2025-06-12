import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Set up the Chrome WebDriver with anti-detection settings"""
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def upload_file(driver, file_path, retry_attempts=3):
    """Upload a file to a file input field with retry logic"""
    for attempt in range(retry_attempts):
        try:
            # First try visible file inputs
            file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            for input_elem in file_inputs:
                try:
                    if input_elem.is_displayed():
                        input_elem.send_keys(file_path)
                        print(f"✓ File uploaded: {os.path.basename(file_path)}")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            # Then try hidden file inputs
            for input_elem in file_inputs:
                try:
                    driver.execute_script("arguments[0].style.display = 'block';", input_elem)
                    input_elem.send_keys(file_path)
                    print(f"✓ File uploaded (hidden input): {os.path.basename(file_path)}")
                    time.sleep(1)
                    return True
                except:
                    continue
            
            # If we're here, try to find upload buttons and click them first
            upload_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Upload') or contains(@aria-label, 'Upload')] | " +
                "//span[contains(text(), 'Upload')] | //label[contains(text(), 'Upload')]")
            
            for button in upload_buttons:
                if button.is_displayed() and button.is_enabled():
                    try:
                        button.click()
                        print("✓ Clicked upload button")
                        time.sleep(1)
                        
                        # Try to find file inputs again
                        file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                        for input_elem in file_inputs:
                            try:
                                input_elem.send_keys(file_path)
                                print(f"✓ File uploaded after button click: {os.path.basename(file_path)}")
                                time.sleep(1)
                                return True
                            except:
                                continue
                    except:
                        continue
            
            if attempt < retry_attempts - 1:
                print(f"⚠️ Upload attempt {attempt+1} failed, retrying...")
                time.sleep(1)
            else:
                print(f"⚠️ Upload failed after {retry_attempts} attempts")
                return False
                
        except Exception as e:
            if attempt < retry_attempts - 1:
                print(f"❌ Upload error: {str(e)[:100]}, retrying...")
                time.sleep(1)
            else:
                print(f"❌ Upload error: {str(e)[:100]}")
                return False
    
    return False

def fill_form_fields(driver):
    """Fill common application form fields"""
    field_mapping = {
        "phone": "9004177451",
        "mobile": "9004177451", 
        "city": "Mumbai",
        "location": "Mumbai",
        "postal": "400001",
        "zip": "400001"
    }
    
    # Fill text inputs
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for field in inputs:
        try:
            field_id = (field.get_attribute("id") or "").lower()
            field_name = (field.get_attribute("name") or "").lower()
            placeholder = (field.get_attribute("placeholder") or "").lower()
            
            # Skip hidden or file inputs
            if field.get_attribute("type") in ["file", "hidden"] or not field.is_displayed():
                continue
                
            # Fill matching fields
            for key, value in field_mapping.items():
                if (key in field_id or key in field_name or key in placeholder) and field.is_enabled():
                    field.clear()
                    field.send_keys(value)
                    print(f"✓ Filled field: {key}")
                    time.sleep(0.5)
        except:
            continue
    
    # Handle checkboxes (usually for terms agreement)
    checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
    for checkbox in checkboxes:
        try:
            if checkbox.is_displayed() and not checkbox.is_selected():
                checkbox.click()
                print("✓ Checked a checkbox")
                time.sleep(0.5)
        except:
            continue

def is_application_successful(driver):
    """Check if the application was submitted successfully"""
    # More comprehensive list of success indicators with broader selectors
    success_indicators = [
        # Text-based indicators
        "//span[contains(text(), 'Application submitted')]",
        "//span[contains(text(), 'Applied')]",
        "//div[contains(text(), 'Application submitted')]",
        "//div[contains(text(), 'Applied')]",
        "//p[contains(text(), 'Application submitted')]",
        "//p[contains(text(), 'Applied')]",
        "//h1[contains(text(), 'Application submitted')]",
        "//h2[contains(text(), 'Application submitted')]",
        "//div[contains(text(), 'Your application was sent')]",
        "//div[contains(text(), 'application was sent')]",
        "//div[contains(text(), 'Application sent')]",
        "//div[contains(text(), 'Thank you for applying')]",
        "//div[contains(text(), 'successfully applied')]",
        
        # Class-based indicators
        "//div[contains(@class, 'success')]",
        "//div[contains(@class, 'applied')]",
        "//div[contains(@class, 'confirmation')]",
        
        # LinkedIn-specific
        "//div[contains(@class, 'artdeco-inline-feedback--success')]",
        "//div[contains(@class, 'jobs-apply-button--applied')]",
        "//button[contains(@class, 'applied')]"
    ]
    
    for indicator in success_indicators:
        try:
            elements = driver.find_elements(By.XPATH, indicator)
            if elements and any(element.is_displayed() for element in elements):
                return True
        except:
            continue
    
    # Check if the apply button text has changed to "Applied"
    try:
        apply_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Apply') or contains(text(), 'Apply')]")
        for button in apply_buttons:
            if "applied" in button.text.lower() or "applied" in (button.get_attribute("aria-label") or "").lower():
                return True
    except:
        pass
        
    # Take a screenshot for debugging
    try:
        screenshot_path = f"application_result_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"✓ Screenshot saved: {screenshot_path}")
    except:
        pass
        
    return False

def apply_for_job(driver, job_url, resume_path):#cover_letter
    """Apply for a single job"""
    try:
        # Navigate to job page
        driver.get(job_url)
        print(f"✓ Navigated to job page")
        time.sleep(3)
        
        # Save the page title for better job identification
        try:
            job_title_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]")
            job_title = job_title_element.text
            print(f"✓ Job title: {job_title}")
        except:
            job_title = "Unknown Title"
            
        # Find and click apply button
        apply_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(@aria-label, 'Apply') or contains(@class, 'jobs-apply')]")
        apply_clicked = False
        
        for button in apply_buttons:
            if button.is_displayed() and button.is_enabled():
                # Save button state for later comparison
                original_text = button.text
                print(f"✓ Found apply button: '{original_text}'")
                
                button.click()
                print("✓ Clicked apply button")
                apply_clicked = True
                time.sleep(3)
                break
                
        if not apply_clicked:
            print("⚠️ Could not find standard apply button, trying alternative selectors")
            
            # Try alternative button selectors
            alt_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'apply') or contains(@class, 'apply')] | //div[contains(@role, 'button')][contains(text(), 'Apply')]")
            for button in alt_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("✓ Clicked alternative apply button")
                    apply_clicked = True
                    time.sleep(3)
                    break
                    
        if not apply_clicked:
            print("❌ Could not find any apply button")
            driver.save_screenshot(f"no_apply_button_{int(time.time())}.png")
            return "Failed to find apply button"
            
        # Upload resume
        upload_success = upload_file(driver, resume_path)
        if not upload_success:
            print("⚠️ Resume upload failed or wasn't needed")
            
        # Look for cover letter field
        #cover_letter_indicators = driver.find_elements(By.XPATH, "//label[contains(text(), 'Cover') or contains(text(), 'cover')] | //h3[contains(text(), 'Cover') or contains(text(), 'cover')]")
        #if cover_letter_indicators:
            #upload_file(driver, cover_letter_path)
            #print("✓ Cover letter upload attempted")
            
        # Fill form fields
        fill_form_fields(driver)
        
        # Click through application steps (next/submit buttons)
        for attempt in range(10):  # Try up to 10 steps in the application process
            time.sleep(2)  # Wait for page to update
            
            # Check if application is already successful after last click
            if is_application_successful(driver):
                print("✓ Application success detected!")
                return "Applied successfully!"
            
            # Look for next/submit buttons
            next_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'submit') or contains(text(), 'Next') or contains(text(), 'next') or contains(text(), 'Continue') or contains(text(), 'continue')] | //button[@type='submit']")
            submit_clicked = False
            
            for button in next_buttons:
                if button.is_displayed() and button.is_enabled():
                    button_text = button.text.strip()
                    if button_text:  # Only click if button has text
                        button.click()
                        print(f"✓ Clicked button: '{button_text}'")
                        submit_clicked = True
                        time.sleep(2)
                        break
                    
            if not submit_clicked:
                # If no standard buttons found, try footer buttons (common in LinkedIn)
                footer_buttons = driver.find_elements(By.XPATH, "//footer//button | //div[contains(@class, 'footer')]//button")
                for button in footer_buttons:
                    if button.is_displayed() and button.is_enabled() and button.text.strip():
                        button.click()
                        print(f"✓ Clicked footer button: '{button.text}'")
                        submit_clicked = True
                        time.sleep(2)
                        break
                        
            if not submit_clicked:
                # If no more buttons, we're probably done or stuck
                print("⚠️ No more buttons found")
                break
                
        # Final check for success
        if is_application_successful(driver):
            print("✓ Application success detected!")
            return "Applied successfully!"
        else:
            print("⚠️ Could not confirm application success")
            # Capture screenshot for review
            try:
                screenshot_path = f"application_result_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                print(f"✓ Final screenshot saved: {screenshot_path}")
            except:
                pass
                
            return "Application completed, but success uncertain"
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        # Take error screenshot
        try:
            driver.save_screenshot(f"error_{int(time.time())}.png")
        except:
            pass
        return f"Error: {str(e)[:100]}"

def search_and_apply_for_jobs(driver, search_term, resume_path, max_jobs=5, 
                             location="", experience_level="", job_type="", date_posted=""):#cover_letter
    """Search for jobs and apply to them with additional filters"""
    try:
        # Navigate to LinkedIn jobs page
        driver.get("https://www.linkedin.com/jobs/")
        print("✓ Navigated to LinkedIn Jobs page")
        time.sleep(3)
        
        # Find and fill the search input
        search_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'Search') or contains(@id, 'jobs-search') or contains(@name, 'keywords')]")
        search_performed = False
        
        for search_input in search_inputs:
            if search_input.is_displayed():
                search_input.clear()
                search_input.send_keys(search_term)
                search_input.send_keys(Keys.RETURN)
                print(f"✓ Searching for: {search_term}")
                search_performed = True
                time.sleep(5)  # Wait for search results
                break
                
        if not search_performed:
            print("⚠️ Could not find search input, trying alternative approach")
            # Try clicking on search box first
            search_boxes = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Search')] | //div[contains(@role, 'search')]")
            for box in search_boxes:
                if box.is_displayed():
                    box.click()
                    time.sleep(1)
                    search_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'Search')]")
                    if search_inputs:
                        search_inputs[0].send_keys(search_term)
                        search_inputs[0].send_keys(Keys.RETURN)
                        print(f"✓ Searching for: {search_term} (alternative method)")
                        search_performed = True
                        time.sleep(5)
                        break
        
        if not search_performed:
            print("❌ Could not perform search")
            return []
            
        # Apply filters (expanded filtering section)
        try:
            filter_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Filters') or contains(@aria-label, 'Filter')]")
            for button in filter_buttons:
                if button.is_displayed():
                    button.click()
                    print("✓ Clicked on filters")
                    time.sleep(2)
                    
                    # Apply Easy Apply filter
                    easy_apply_checkboxes = driver.find_elements(By.XPATH, "//label[contains(text(), 'Easy Apply')]")
                    for checkbox in easy_apply_checkboxes:
                        if checkbox.is_displayed():
                            checkbox.click()
                            print("✓ Selected Easy Apply filter")
                            time.sleep(1)
                    
                    # Apply Location filter
                    if location:
                        location_inputs = driver.find_elements(By.XPATH, "//input[contains(@id, 'location') or contains(@name, 'location')]")
                        for loc_input in location_inputs:
                            if loc_input.is_displayed():
                                loc_input.clear()
                                loc_input.send_keys(location)
                                print(f"✓ Set location filter: {location}")
                                time.sleep(1)
                    
                    # Apply Experience Level filter
                    if experience_level:
                        exp_dropdowns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Experience Level')]")
                        for dropdown in exp_dropdowns:
                            if dropdown.is_displayed():
                                dropdown.click()
                                time.sleep(1)
                                exp_options = driver.find_elements(By.XPATH, f"//label[contains(text(), '{experience_level}')]")
                                for option in exp_options:
                                    if option.is_displayed():
                                        option.click()
                                        print(f"✓ Set experience level: {experience_level}")
                                        time.sleep(1)
                                        break
                    
                    # Apply Job Type filter
                    if job_type:
                        type_dropdowns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Job Type')]")
                        for dropdown in type_dropdowns:
                            if dropdown.is_displayed():
                                dropdown.click()
                                time.sleep(1)
                                type_options = driver.find_elements(By.XPATH, f"//label[contains(text(), '{job_type}')]")
                                for option in type_options:
                                    if option.is_displayed():
                                        option.click()
                                        print(f"✓ Set job type: {job_type}")
                                        time.sleep(1)
                                        break
                    
                    # Apply Date Posted filter
                    if date_posted:
                        date_dropdowns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Date Posted')]")
                        for dropdown in date_dropdowns:
                            if dropdown.is_displayed():
                                dropdown.click()
                                time.sleep(1)
                                date_options = driver.find_elements(By.XPATH, f"//label[contains(text(), '{date_posted}')]")
                                for option in date_options:
                                    if option.is_displayed():
                                        option.click()
                                        print(f"✓ Set date posted: {date_posted}")
                                        time.sleep(1)
                                        break
                    
                    # Click show results button
                    show_results = driver.find_elements(By.XPATH, "//button[contains(text(), 'Show') or contains(text(), 'Apply') or contains(text(), 'Done')]")
                    if show_results:
                        for button in show_results:
                            if button.is_displayed() and button.is_enabled():
                                button.click()
                                print("✓ Applied filters")
                                time.sleep(3)
                                break
                    break
        except Exception as e:
            print(f"⚠️ Could not apply filters: {str(e)[:100]}")
            
        # Find job listings
        job_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container') or contains(@class, 'job-search-card')]")
        if not job_cards:
            job_cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/jobs/view/')]")
            
        if not job_cards:
            # Try a more generic approach
            job_cards = driver.find_elements(By.XPATH, "//li[contains(@class, 'job-result-card') or contains(@class, 'jobs-search-result-item')]")
            
        if len(job_cards) > 0:
            print(f"✓ Found {len(job_cards)} job listings")
        else:
            print("❌ No job listings found")
            driver.save_screenshot("no_jobs_found.png")
            return []
        
        results = []
        applied_count = 0
        
        # Process each job
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                # Extract job info
                try:
                    job_title_elem = card.find_element(By.XPATH, ".//h3 | .//a[contains(@class, 'job-title')]")
                    job_title = job_title_elem.text
                except:
                    try:
                        job_title_elem = card.find_element(By.XPATH, ".//a")
                        job_title = job_title_elem.text
                    except:
                        job_title = "Unknown Title"
                    
                try:
                    company_elem = card.find_element(By.XPATH, ".//h4 | .//a[contains(@class, 'company')]")
                    company = company_elem.text
                except:
                    company = "Unknown Company"
                    
                # Get job link
                try:
                    job_link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                except:
                    try:
                        job_link = card.get_attribute("href")
                    except:
                        print(f"⚠️ Could not get link for job {i+1}")
                        continue
                        
                print(f"\n🔶 Job {i+1}: {job_title} at {company}")
                
                # Apply for the job
                status = apply_for_job(driver, job_link, resume_path)#cover_letter
                results.append({"title": job_title, "company": company, "link": job_link, "status": status})
                
                if "Applied successfully" in status:
                    applied_count += 1
                    
                print(f"📊 Status: {status}")
                time.sleep(3)  # Wait between applications
                
            except Exception as e:
                print(f"❌ Error processing job {i+1}: {str(e)[:100]}")
                
        print(f"\n✅ Applied to {applied_count} out of {len(results)} processed jobs")
        return results
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return []
    
def search_and_apply_for_jobs_indeed(driver, search_term, resume_path, max_jobs=5,
                                    location="", experience_level="", job_type="", date_posted=""):
    """Search for jobs on Indeed and apply to them with additional filters"""
    try:
        # Navigate to Indeed jobs page
        driver.get("https://www.indeed.com/")
        print("✓ Navigated to Indeed.com")
        time.sleep(3)
        
        # Find and fill the search inputs
        search_performed = False
        
        # Find the "what" (job title) input field
        what_inputs = driver.find_elements(By.XPATH, 
            "//input[@id='text-input-what' or @name='q' or contains(@placeholder, 'Job title') or contains(@placeholder, 'what')]")
        
        # Find the "where" (location) input field  
        where_inputs = driver.find_elements(By.XPATH,
            "//input[@id='text-input-where' or @name='l' or contains(@placeholder, 'City') or contains(@placeholder, 'where')]")
        
        # Fill the search fields
        if what_inputs and what_inputs[0].is_displayed():
            what_inputs[0].clear()
            what_inputs[0].send_keys(search_term)
            print(f"✓ Entered search term: {search_term}")
            
            if where_inputs and where_inputs[0].is_displayed() and location:
                where_inputs[0].clear()
                where_inputs[0].send_keys(location)
                print(f"✓ Entered location: {location}")
            
            # Click search button or press Enter
            search_buttons = driver.find_elements(By.XPATH, 
                "//button[@type='submit' or contains(@class, 'yosegi-InlineWhatWhere-primaryButton')]")
            
            if search_buttons and search_buttons[0].is_displayed():
                search_buttons[0].click()
                print("✓ Clicked search button")
                search_performed = True
            else:
                what_inputs[0].send_keys(Keys.RETURN)
                print("✓ Pressed Enter to search")
                search_performed = True
                
            time.sleep(5)  # Wait for search results
            
        if not search_performed:
            print("❌ Could not perform search")
            return []
            
        # Apply filters if specified
        try:
            # Look for filter dropdowns
            if experience_level:
                exp_buttons = driver.find_elements(By.XPATH,
                    "//button[contains(@aria-label, 'Experience Level') or contains(text(), 'Experience')]")
                for button in exp_buttons:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        exp_links = driver.find_elements(By.XPATH, 
                            f"//a[contains(text(), '{experience_level}')]")
                        for link in exp_links:
                            if link.is_displayed():
                                link.click()
                                print(f"✓ Applied experience filter: {experience_level}")
                                time.sleep(2)
                                break
                        break
                        
            if job_type:
                type_buttons = driver.find_elements(By.XPATH,
                    "//button[contains(@aria-label, 'Job Type') or contains(text(), 'Job Type')]")
                for button in type_buttons:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        type_links = driver.find_elements(By.XPATH,
                            f"//a[contains(text(), '{job_type}')]")
                        for link in type_links:
                            if link.is_displayed():
                                link.click()
                                print(f"✓ Applied job type filter: {job_type}")
                                time.sleep(2)
                                break
                        break
                        
            if date_posted:
                date_buttons = driver.find_elements(By.XPATH,
                    "//button[contains(@aria-label, 'Date Posted') or contains(text(), 'Date')]")
                for button in date_buttons:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        # Map common date filters
                        date_map = {
                            "Past 24 hours": "1",
                            "Past 3 days": "3", 
                            "Past week": "7",
                            "Past 2 weeks": "14",
                            "Past month": "30"
                        }
                        date_value = date_map.get(date_posted, date_posted)
                        date_links = driver.find_elements(By.XPATH,
                            f"//a[contains(@href, 'fromage={date_value}') or contains(text(), '{date_posted}')]")
                        for link in date_links:
                            if link.is_displayed():
                                link.click()
                                print(f"✓ Applied date filter: {date_posted}")
                                time.sleep(2)
                                break
                        break
                        
        except Exception as e:
            print(f"⚠️ Could not apply filters: {str(e)[:100]}")
            
        # Find job listings
        job_cards = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'job_seen_beacon')] | //div[contains(@class, 'slider_container')] | //div[contains(@class, 'jobsearch-SerpJobCard')]")
        
        if not job_cards:
            # Try alternative selectors
            job_cards = driver.find_elements(By.XPATH,
                "//a[contains(@data-jk, '')] | //h2[contains(@class, 'jobTitle')]/parent::* | //span[@title]//parent::h2//parent::*")
                
        if not job_cards:
            # Generic approach for job cards
            job_cards = driver.find_elements(By.XPATH,
                "//div[contains(@class, 'result')] | //article | //li[contains(@class, 'result')]")
                
        if len(job_cards) > 0:
            print(f"✓ Found {len(job_cards)} job listings")
        else:
            print("❌ No job listings found")
            driver.save_screenshot("no_indeed_jobs_found.png")
            return []
            
        results = []
        applied_count = 0
        
        # Process each job
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                # Extract job info
                try:
                    job_title_elem = card.find_element(By.XPATH, 
                        ".//h2//a | .//span[@title] | .//a[contains(@data-jk, '')]")
                    job_title = job_title_elem.get_attribute("title") or job_title_elem.text
                except:
                    try:
                        job_title_elem = card.find_element(By.XPATH, ".//a")
                        job_title = job_title_elem.text
                    except:
                        job_title = "Unknown Title"
                        
                try:
                    company_elem = card.find_element(By.XPATH,
                        ".//span[@class='companyName'] | .//a[contains(@data-testid, 'company')] | .//span[contains(@class, 'company')]")
                    company = company_elem.text
                except:
                    company = "Unknown Company"
                    
                # Get job link
                try:
                    job_link_elem = card.find_element(By.XPATH, 
                        ".//h2//a | .//a[contains(@data-jk, '')]")
                    job_link = job_link_elem.get_attribute("href")
                    
                    # Convert relative URLs to absolute URLs
                    if job_link and job_link.startswith("/"):
                        job_link = "https://www.indeed.com" + job_link
                        
                except:
                    print(f"⚠️ Could not get link for job {i+1}")
                    continue
                    
                print(f"\n🔶 Job {i+1}: {job_title} at {company}")
                
                # Apply for the job using the existing apply_for_job function
                status = apply_for_job(driver, job_link, resume_path)
                results.append({"title": job_title, "company": company, "link": job_link, "status": status})
                
                if "Applied successfully" in status:
                    applied_count += 1
                    
                print(f"📊 Status: {status}")
                time.sleep(3)  # Wait between applications
                
            except Exception as e:
                print(f"❌ Error processing job {i+1}: {str(e)[:100]}")
                
        print(f"\n✅ Applied to {applied_count} out of {len(results)} processed jobs")
        return results
        
    except Exception as e:
        print(f"❌ Indeed search error: {str(e)}")
        return []

def main():
    print("\n=== LinkedIn Job Application Bot ===\n")
    
    # Set up file paths - adjust these to your files
    resume_path = os.path.abspath("Danish_CV.pdf")
    #cover_letter_path = os.path.abspath("Hitesh_Cover_Letter.pdf")
    
    # Check if files exist
    if not os.path.exists(resume_path):
        print(f"❌ Resume not found: {resume_path}")
        resume_path = input("Enter the full path to your resume PDF: ")
        if not os.path.exists(resume_path):
            print("Invalid path. Exiting.")
            return
            
    #if not os.path.exists(cover_letter_path):
     #   print(f"❌ Cover letter not found: {cover_letter_path}")
      #  cover_letter_path = input("Enter the full path to your cover letter PDF: ")
       # if not os.path.exists(cover_letter_path):
        #    print("Invalid path. Exiting.")
         #   return
        
    # Initialize browser
    print("🌐 Setting up browser...")
    driver = setup_driver()
    
    # Login to LinkedIn
    driver.get("https://www.linkedin.com/login")
    print("\n⚠️ Please log in to LinkedIn manually")
    input("Press Enter once you've logged in...")
    
    # Job search parameters
    search_term = input("\nEnter job search term (e.g., 'Python Developer'): ")
    
    # Additional filter options
    print("\n=== Optional Filter Settings ===")
    print("(Press Enter to skip any filter)")
    
    location = input("Location (e.g., 'Remote', 'New York'): ")
    
    print("\nExperience Level Options:")
    print("1. Internship")
    print("2. Entry level")
    print("3. Associate")
    print("4. Mid-Senior level")
    print("5. Director")
    experience_input = input("Experience Level (enter number or name): ")
    
    experience_map = {
        "1": "Internship", 
        "2": "Entry level", 
        "3": "Associate", 
        "4": "Mid-Senior level", 
        "5": "Director"
    }
    
    experience_level = experience_map.get(experience_input, experience_input)
    
    print("\nJob Type Options:")
    print("1. Full-time")
    print("2. Part-time")
    print("3. Contract")
    print("4. Temporary")
    print("5. Internship")
    job_type_input = input("Job Type (enter number or name): ")
    
    job_type_map = {
        "1": "Full-time", 
        "2": "Part-time", 
        "3": "Contract", 
        "4": "Temporary", 
        "5": "Internship"
    }
    
    job_type = job_type_map.get(job_type_input, job_type_input)
    
    print("\nDate Posted Options:")
    print("1. Past 24 hours")
    print("2. Past week")
    print("3. Past month")
    date_posted_input = input("Date Posted (enter number or name): ")
    
    date_posted_map = {
        "1": "Past 24 hours", 
        "2": "Past week", 
        "3": "Past month"
    }
    
    date_posted = date_posted_map.get(date_posted_input, date_posted_input)
    
    try:
        max_jobs = int(input("\nHow many jobs to apply for (max)? "))
    except:
        print("Invalid number, defaulting to 5")
        max_jobs = 5
    
    # Execute search and application
    print(f"\n🚀 Searching and applying for '{search_term}' jobs...")
    results = search_and_apply_for_jobs(
        driver, 
        search_term, 
        resume_path,  
        max_jobs,
        location=location,
        experience_level=experience_level,
        job_type=job_type,
        date_posted=date_posted
    )
    
    # Display results
    print("\n=== Application Results ===")
    successful_applications = 0
    for i, job in enumerate(results):
        print(f"{i+1}. {job['title']} at {job['company']}: {job['status']}")
        if "Applied successfully" in job['status']:
            successful_applications += 1
    
    # Final summary
    print(f"\n🎯 Successfully applied to {successful_applications} out of {len(results)} jobs")
    print("\n🏁 Process complete!")
    
    # Save results to file
    try:
        with open("application_results.txt", "w") as file:
            file.write(f"LinkedIn Job Applications - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Search Term: {search_term}\n\n")
            for i, job in enumerate(results):
                file.write(f"{i+1}. {job['title']} at {job['company']}\n")
                file.write(f"   Status: {job['status']}\n")
                file.write(f"   Link: {job['link']}\n\n")
        print("✓ Results saved to application_results.txt")
    except:
        print("⚠️ Could not save results to file")
    
    input("Press Enter to close the browser...")
    driver.quit()

# Wrap main execution in a callable function
def run_job_automation(search_term, resume_path, max_jobs=5,
                       location="", experience_level="", job_type="", date_posted=""):
    driver = setup_driver()
    results = search_and_apply_for_jobs(
        driver,
        search_term,
        resume_path,
        max_jobs,
        location,
        experience_level,
        job_type,
        date_posted
    )
    driver.quit()
    return results

if __name__ == "__main__":
    main()