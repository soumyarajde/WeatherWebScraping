from pathlib import Path
from bs4 import BeautifulSoup
import datetime
import h5py
import csv
import requests
import pandas as pd


class WeatherSource:
    """
    Abstract class for extracting weather information from an HTML source.
    This class provides functionality to read a weather report HTML file—either from a local path
    or via HTTP(S) and parse it using BeautifulSoup.Subclasses should implement the method
    get_high_low() to extract specific weather data.

    Attributes:
        html_path : str
        Path to a local HTML file or a URL to an HTML page containing weather data.
    """

    def __init__(self, html_path: str):
        """
        Initialize the WeatherSource object.
        Args:
            html_path : str
            Path to the local HTML file or a URL.
        """

        self.html_path = html_path

    def _get_soup(self):
        """
        Load and parse the HTML source.If the provided path exists locally, loads the file, otherwise, attempts
        to download the contents over HTTP using rwquests.
        Returns:
            soup : BeautifulSoup
            BeautifulSoup object representing the parsed HTML document.
        Raises:
            requests.exceptions.RequestException
            If the HTML cannot be downloaded from the given URL.

        """
        # read  the local HTML file
        if Path(self.html_path).exists():
            html_content = Path(self.html_path).read_text(encoding="utf-8")
        else:
            # set custom user agent
            headers = {
                "User-Agent": "EducationalWebScrapingBot/1.0 (https://www.iu-akademie.de/weiterbildungen/data-analyst-python/)"
            }

            # read the content of URL provided over HTTP
            response = requests.get(self.html_path, headers=headers, timeout=15)
            response.raise_for_status()
            html_content = response.text
        # parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")
        return soup

    def get_high_low(self):
        """
        Abstract method for extracting the high and low temperature values for the specified weather source.
        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_high_low().")


class StadtReutlingenSource(WeatherSource):
    """
    Subclass of WeatherSource representing weather source  Reutlingen city.
    Inherited parameter:
        html_path : str
        Path or URL to the HTML file containing weather data.
    """

    def get_high_low(self):
        """
        Extracts today's high and low temperature values for Stadt Reutlingen.

        The method parses the HTML and searches for two <span> elements with class names
        'hitWeather_averageTempMax' (for high) and 'hitWeather_averageTempMin' (for low).
        It then retrieves the digit characters from their contents and returns them as integers.
        Returns:
            tuple of (int, int)
            High and low temperature values, in their integer representations.
        Raises:
            ValueError
            If either temperature span cannot be found in the page.
        """

        soup = self._get_soup()
        # locate the two <span> elements via their class attribute
        high_span = soup.find("span", class_="hitWeather_averageTempMax")
        low_span = soup.find("span", class_="hitWeather_averageTempMin")

        if high_span is None or low_span is None:
            raise ValueError("Could not find  temperature spans.")

        # extract the text and keep only the digits
        high_value = int(
            "".join(ch for ch in high_span.get_text(strip=True) if ch.isdigit())
        )
        low_value = int(
            "".join(ch for ch in low_span.get_text(strip=True) if ch.isdigit())
        )

        return high_value, low_value


class WetterComSource(WeatherSource):
    """
    Subclass of WeatherSource representing weather source  Wetter.com.
    Inherited parameter:
        html_path : str
        Path or URL to the HTML file containing weather data.
    """

    def get_high_low(self):
        """
        Extracts today's high and low temperature values for Stadt Reutlingen.

        The method parses the HTML and searches for two <span> elements with class names
        'forecast-navigation-temperature-max' (for high) and 'forecast-navigation-temperature-min' (for low).
        It then retrieves the digit characters from their contents and returns them as integers.
        Returns:
            tuple of (int, int)
            High and low temperature values, in their integer representations.
        Raises:
            ValueError
            If either temperature span cannot be found in the page.
        """

        soup = self._get_soup()
        # locate the two <span> elements via their class attribute
        high_span = soup.find("span", class_="forecast-navigation-temperature-max")
        low_span = soup.find("span", class_="forecast-navigation-temperature-min")

        if high_span is None or low_span is None:
            raise ValueError("Could not find temperature spans.")

        # extract the text and keep only the digits
        high_value = int(
            "".join(ch for ch in high_span.get_text(strip=True) if ch.isdigit())
        )
        low_value = int(
            "".join(ch for ch in low_span.get_text(strip=True) if ch.isdigit())
        )

        return high_value, low_value


class WetterNetSource(WeatherSource):
    """
    Subclass of WeatherSource representing weather source wetter.net.
    Inherited parameter:
        html_path : str
        Path or URL to the HTML file containing weather data.
    """

    def get_high_low(self):
        """
        Extracts today's high and low temperatures from wetter.net HTML.

        This method looks for <h2> tags with the classes 'white', 'center', 'tempText', and 'todayText'
        which are supposed to represent temperature values (first for high, second for low). It extracts
        the digit characters from their contents and returns them as integers.
        Returns:
            tuple of (int, int)
            High and low temperature values, in their integer representations.
        Raises:
            ValueError
            If high or low temperature values could not be extracted/found.

        """

        soup = self._get_soup()

        temp_tags = soup.find_all(
            "h2", class_=["white", "center", "tempText", "todayText"]
        )  # <-- same for high & low now

        # Keep the original variable names even though their meaning changed
        high_tag = temp_tags[0] if temp_tags else None
        low_tag = temp_tags[1] if len(temp_tags) > 1 else None

        if high_tag is None or low_tag is None:
            raise ValueError(
                "Could not find high and low temperature tags in wetter.net HTML."
            )

        # extract the text and keep only the digits
        high_value = int(
            "".join(ch for ch in high_tag.get_text(strip=True) if ch.isdigit())
        )
        low_value = int(
            "".join(ch for ch in low_tag.get_text(strip=True) if ch.isdigit())
        )

        return high_value, low_value


class WeatherDataManager:
    """
    Manages weather data collection from various sources and storage in an HDF5 file.
    This class is responsible for reading a CSV file containing weather source names and URLs, capturing weather data using specific WeatherSource subclasses
    and storing weather data (high/low temperatures) in an HDF5 file, organized by date and source.

    Attributes:
        hdf5_path (str): Path to the output HDF5 file.
        urls_csv (str): Path to the CSV file listing sources and URLs.
    """

    def __init__(self, hdf5_path: str = None, urls_csv: str = None):
        """
        Initializes the WeatherDataManager.

        Args:
            hdf5_path (str): Path to the HDF5 file where data will be stored.
            urls_csv (str): Path to the CSV file containing weather sources and URLs.
        """
        self.hdf5_path = hdf5_path
        self.urls_csv = urls_csv

    def store_in_hdf5(self, high_temp: int, low_temp: int, hdf5_file: str, source: str):
        """
        Store high and low temperature values for a given source and current date in an HDF5 file.
        Temperatures are stored under a group named by date (ISO format), with subgroups for each source.
        If datasets already exist for the date/source, they will be replaced.

        Args:
            high_temp (int): The high temperature to store.
            low_temp (int): The low temperature to store.
            hdf5_file (str): Path to the HDF5 file in which to store the data.
            source (str): Name of the weather data source.
        """

        # Get the current date in ISO format
        date_key = datetime.date.today().isoformat()

        # Create a DataFrame with a single row of the current data
        df = pd.DataFrame(
            {
                "date": [date_key],
                "source": [source],
                "high_temp": [high_temp],
                "low_temp": [low_temp],
            }
        )
        # Make sure  dtypes for the numeric columns are *always* float64
        df = df.astype({"high_temp": "float64", "low_temp": "float64"})
        # Append the data to an HDF5 file in table format
        # Use 'a' mode to append data, and 'weather_data' as the key in the store
        df.to_hdf(
            hdf5_file,
            key="weather",
            mode="a",
            format="table",
            append=True,
            data_columns=True,
        )

    def capture_weather(self):
        """
        Fetch weather data for each source listed in the CSV, and store results in HDF5.
        For each row in the CSV file (with columns 'source' and 'url'), instantiate the
        corresponding WeatherSource subclass, extract today's high and low temperature,
        and store it in the HDF5 file.
        Raises:
            FileNotFoundError: If the CSV file cannot be opened.
        """
        hdf5_path = self.hdf5_path
        urls_csv = self.urls_csv
        source_classes = {
            "stadt_reutlingen": StadtReutlingenSource,
            "wetter_com": WetterComSource,
            "wetter_net": WetterNetSource,
        }

        with open(urls_csv, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                source = row["source"]
                url = row["url"]
                if source not in source_classes:
                    print(f"Unsupported source: {source}")
                    continue
                src_cls = source_classes[source]
                src_instance = src_cls(url)
                high_temp, low_temp = src_instance.get_high_low()
                print(f"{source:<15} → High: {high_temp}°C | Low: {low_temp}°C")
                self.store_in_hdf5(high_temp, low_temp, hdf5_path, source)

        print(f"All values stored in {hdf5_path}")


if __name__ == "__main__":
    # Instantiate WeatherDataManager with path to HDF5 file and csv source list
    weather_manager = WeatherDataManager(
        "weather_combined_sort_v2.h5", "weather_sources.csv"
    )

    weather_manager.capture_weather()
