# Project: Weather Data Archiving and Analysis App

**Author:** Jakub Hościło

### 1. Project Description
This application is designed to fetch and present meteorological data from across Poland, utilizing the public API provided by the Institute of Meteorology and Water Management - National Research Institute (https://danepubliczne.imgw.pl/api/data/synop). Data is visualized through interactive tables and charts.

### 2. Key Features
* **Data Retrieval:** Automated fetching of synoptic data using the `requests` library. Includes built-in dialog alerts for connection errors and database update status.
* **Storage Management:** Data is stored in the `./data` directory in both `weather_history.json` and `weather_history.db` formats. While JSON serves as a backup/transport layer, the core application logic and queries are powered by an optimized SQLite database. Both systems include duplicate prevention logic.
* **Search and Filtering:** Advanced filtering capabilities for all physical quantities provided by IMGW, including station name, day of the week, exact date, date ranges, temperature, wind speed/direction, humidity, precipitation, and pressure.
* **Statistics:** Automatic calculation of mean, minimum, and maximum values for filtered results, including identification of specific stations where extreme values occurred.
* **Data Visualization:** A dedicated tab for generating time-series charts for selected weather parameters and stations using the `matplotlib` library.

### 3. Application Structure
The program follows a modular design divided into two main components:
* **backend.py:** Contains the `DataJson` class (API management and file I/O) and the `SqlDataFilters` class (SQL engine and statistical analysis).
* **main.py:** The Graphical User Interface (GUI) built with PyQt6. It handles signal-slot mechanisms, event management, and data presentation.

### 4. Data Source and Legal Disclaimer
* **Source:** This application uses data provided by the **Institute of Meteorology and Water Management - National Research Institute (IMGW-PIB)**.
* **Data Processing:** Raw JSON data is processed, archived in a local SQLite database, and visualized for educational purposes.
* **License:** This project is strictly non-commercial and was developed for educational use in accordance with the IMGW-PIB data usage regulations.
* *Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej - Państwowy Instytut Badawczy.<br>
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały
przetworzone.*

### 5. Technical Requirements, How to Run
Required libraries are listed in `requirements.txt`:
* `PyQt6`
* `requests`
* `matplotlib`

To launch the application: `python main.py`

### 6. Usage Notes
A sample dataset is provided in the `./data_example` directory. To test the application's filtering and charting capabilities with historical data immediately, copy the contents of this folder into the `./data` directory.

### 7. Future Roadmap
- Implementation of multi-language support (I18n).
- Migration from hardcoded paths to a configuration file (`config.ini` or `.env`).
- Implementation of `QThreads` for asynchronous API calls to prevent UI freezing.