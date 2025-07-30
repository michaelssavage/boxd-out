
import re
import time
from typing import Any, Dict

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class SingleMovieScraper:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._setup_driver_options()
    
    def _setup_driver_options(self) -> Options:
        """Setup Chrome driver options with anti-detection measures"""
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-web-security')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        return self.chrome_options
    
    def scrape_movie(self, movie_title: str) -> Dict[str, Any]:
        """
        Scrape a single movie from Letterboxd
        
        Args:
            movie_title: Movie title slug (e.g., 'bring-her-back')
            
        Returns:
            Dictionary with movie data
            
        Raises:
            Exception: If scraping fails
        """
        url = f"https://letterboxd.com/film/{movie_title}/"
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # Navigate and wait
            driver.get(url)
            
            # More robust waiting strategy
            wait = WebDriverWait(driver, self.timeout)
            
            # Wait for the page to fully load
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Wait for poster-list section to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.poster-list")))
            
            # Additional wait for any lazy loading
            time.sleep(2)
            
            html_content = driver.page_source
            
        except TimeoutException as e:
            raise Exception(f"Failed to load movie page: timeout - {str(e)}")
        except WebDriverException as e:
            raise Exception(f"Failed to load movie page: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during scraping: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        return self._parse_movie_from_html(html_content, url)
    
    def _parse_movie_from_html(self, html_content: str, original_url: str) -> Dict[str, Any]:
        """Parse movie data from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            raise Exception(f"Failed to parse HTML: {str(e)}")
        
        # Find the poster-list section
        poster_section = soup.select_one("section.poster-list")
        if not poster_section:
            raise Exception("Could not find poster-list section on the page")
        
        # Extract movie data from the section
        movie_data = self._extract_movie_data_from_section(poster_section, original_url)
        
        if not movie_data:
            raise Exception("Failed to extract movie data from page")
        
        return movie_data
    
    def _extract_movie_data_from_section(self, section, original_url: str) -> Dict[str, Any]:
        """
        Extract movie data from the poster-list section
        
        Returns:
            Dictionary matching Django Movie model fields
        """
        # Look for film poster within the section
        poster = section.select_one(".film-poster")
        if not poster:
            raise Exception("Could not find film poster in section")
        
        # Extract data from poster attributes
        title = poster.get('data-film-name', '').strip()
        year = poster.get('data-film-release-year', '').strip()
        
        # Ensure we have required data
        if not title:
            raise Exception("Movie title not found")
        
        # If year not found in data attribute, try to extract from frame-title
        if not year:
            frame_title = section.select_one(".frame-title")
            if frame_title:
                year_match = re.search(r'\((\d{4})\)$', frame_title.get_text().strip())
                year = year_match.group(1) if year_match else ''
        
        # Extract image URL
        img_tag = poster.select_one('img')
        image_url = img_tag.get('src', '').strip() if img_tag else ''
        
        # For single movie pages, the link_url is the current page URL
        link_url = original_url
        
        return {
            'title': title,
            'year': year,
            'image_url': image_url,
            'link_url': link_url,
        }