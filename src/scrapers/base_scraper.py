"""Abstract base scraper with common scraping functionality."""

import abc

import requests  # type: ignore


class BaseScraper(abc.ABC):
    """Base class for all scrapers."""

    def __init__(self, base_url: str):
        """Initialize the scraper.

        Args:
            base_url: Base URL for the website to scrape
        """
        self.base_url = base_url
        self.session = requests.Session()

    def get_html_content(self, path: str) -> str:
        """Get HTML content from a URL.

        Args:
            path: Path to append to the base URL

        Returns:
            str: HTML content of the page

        Raises:
            Exception: If there was an error fetching the page or the status code is not 200
        """
        try:
            url = f'{self.base_url}{path}'
            response = self.session.get(url)

            if response.status_code != 200:
                raise Exception(  # pylint: disable=broad-exception-raised
                    f'Failed to fetch URL: {url}, status code: {response.status_code}'
                )

            return response.text
        except Exception as e:
            # Re-raise any exceptions
            raise Exception(  # pylint: disable=broad-exception-raised
                f'Error fetching URL: {self.base_url}{path}'
            ) from e

    @abc.abstractmethod
    def parse_zones(self):
        """Parse the HTML content and extract zone information.

        This method must be implemented by all scraper subclasses.

        Returns:
            list: List of Zone objects
        """
        raise NotImplementedError('Subclasses must implement parse_zones method')
