import re
import time
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class LetterboxdScraper:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._setup_driver_options()
    
    def _setup_driver_options(self) -> Options:
        """Setup Chrome driver options with anti-detection measures"""
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        return self.chrome_options
    
    def scrape_favourites(self, username: str) -> List[Dict[str, Any]]:
        """
        Scrape favorites from Letterboxd user profile
        
        Args:
            username: Letterboxd username
            
        Returns:
            List of movie dictionaries matching Django Movie model structure
            
        Raises:
            Exception: If scraping fails
        """
        url = f"https://letterboxd.com/{username}/"
        
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
            
            # Wait for favorites section
            wait.until(EC.presence_of_element_located((By.ID, "favourites")))
            
            # Wait for poster containers to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#favourites .poster-container")))
            
            # Additional wait for any lazy loading
            time.sleep(2)
            
            html_content = driver.page_source
            
        except TimeoutException as e:
            raise Exception(f"Failed to load page: timeout - {str(e)}")
        except WebDriverException as e:
            raise Exception(f"Failed to load page: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during scraping: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        return self._parse_movies_from_html(html_content)
    
    def _parse_movies_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse movies from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            raise Exception(f"Failed to parse HTML: {str(e)}")
        
        movies = []
        poster_containers = soup.select("#favourites .poster-container")
        
        for container in poster_containers:
            try:
                movie = self._extract_movie_data(container)
                if movie:
                    movies.append(movie)
            except Exception as e:
                # Log individual movie extraction errors but continue
                print(f"Warning: Failed to extract movie data: {str(e)}")
                continue
        
        if len(movies) == 0:
            raise Exception("No movies found, possibly failed to load dynamic content")
        
        return movies
    
    def _extract_movie_data(self, container) -> Dict[str, Any]:
        """
        Extract movie data from a poster container
        
        Returns:
            Dictionary matching Django Movie model fields:
            - title (TextField)
            - year (TextField) 
            - image_url (TextField)
            - link_url (TextField)
            Note: status will be set in the repository layer
        """
        poster = container.select_one(".film-poster")
        if not poster:
            return None
        
        title = poster.get('data-film-name', '').strip()
        year = poster.get('data-film-release-year', '').strip()
        
        # Ensure we have required data
        if not title:
            print("Warning: Movie missing title, skipping")
            return None
        
        if not year:
            frame_title = container.select_one(".frame-title")
            if frame_title:
                year_match = re.search(r'\((\d{4})\)$', frame_title.get_text().strip())
                year = year_match.group(1) if year_match else ''
                
        
        img_tag = poster.select_one('img')
        image_url = img_tag.get('src', '').strip() if img_tag else ''
        
        film_link = poster.get('data-film-link', '').strip()
        link_url = f"https://letterboxd.com{film_link}" if film_link else ''
        
        return {
            'title': title,
            'year': year,
            'image_url': image_url,
            'link_url': link_url, 
        }


def scrape_favourites(username: str) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape favorites
    
    Args:
        username: Letterboxd username
        
    Returns:
        List of movie dictionaries matching Django Movie model structure
    """
    scraper = LetterboxdScraper()
    return scraper.scrape_favourites(username)
