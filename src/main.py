import sys
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QHeaderView, QPushButton, QApplication, QVBoxLayout, QLabel, QMessageBox, QRadioButton, QComboBox, QHBoxLayout, QDoubleSpinBox, QMainWindow, QGroupBox, QCalendarWidget, QTabWidget  
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from backend import SqlDataFilters, DataJson





def displayTableData(table:QTableWidget,columns:list , data:list[dict]) -> None:
    """
    To be used in both main table and stats table, pass SELF as table
    Fills given table with given data, cell by cell
    """
    table.setRowCount(len(data))
    table.setSortingEnabled(False)

    for row, record in enumerate(data):
        for column, key in enumerate(columns):
            val = record.get(key)
            item = QTableWidgetItem()


            if val is not None:
                if type(val) == int or type(val) == float:
                    item.setData(Qt.ItemDataRole.DisplayRole,val)
                else:
                    item.setText(str(val))
            else:
                item.setText("-")
            table.setItem(row, column,item)

            
    table.setSortingEnabled(True)

class MainWeatherTable(QTableWidget):
    """
    Main table displaying all records
    """
    def __init__(self) -> None:
        super().__init__()

        headers: list[str] = ["Stacja", "Data", "Godzina", "Temperatura", "Prędkość wiatru", "Kierunek wiatru", "Wilgotność względna", "Suma opadu", "Ciśnienie"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)   # pyright: ignore[reportOptionalMemberAccess]

    def displayData(self, data: list[dict]) -> None:
        """Fills table with data; uses displayTableData"""
        columns: list[str] = ["stacja", "data_pomiaru", "godzina_pomiaru","temperatura", "predkosc_wiatru", "kierunek_wiatru","wilgotnosc_wzgledna", "suma_opadu", "cisnienie"]
        displayTableData(self, columns, data)


class StatisticsTable(QTableWidget):
    """
    Secondary table displaying statistical data
    """
    def __init__(self) -> None:
        super().__init__()

        headers: list[str] = ["Wielkość", "Średnia", "Minimum", "Wystąpienie MIN", "Maksimum", "Wystąpienie MAX"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # pyright: ignore[reportOptionalMemberAccess]

    def displayData(self, data: list[dict]) -> None:
        """Fills table with data; uses displayTableData"""
        columns: list[str] = ["analyzed_column", "avg", "min", "min_station", "max","max_station"]

        displayTableData(self, columns, data)

class DownloadButton(QPushButton):
    """
    Connects to the API, emits dict signal with status
    """
    statusUpdated = pyqtSignal(dict)
    def __init__(self,backend_manager:DataJson) -> None:
        super().__init__()
        self.backend: DataJson = backend_manager
        
        self.setText("Pobierz Dane")
        self.clicked.connect(self.updateData)
    
    def updateData(self) -> None:
        self.setEnabled(False)
        self.setText("Pobieram")
        QApplication.processEvents()

        self.backend.updateAll()
        self.statusUpdated.emit(self.backend.status)
        
        self.setEnabled(True)
        self.setText("Pobierz Dane")

class DisplayStatus(QWidget):
    """
    Group of QLabels displaying connection status (to API, json, etc.)
    """
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout()

        self.label_online_api = QLabel("Połączenie z API: [...]")
        self.label_offline_read = QLabel("Odczyt z pliku (json): [...]")
        self.label_offline_save = QLabel("Zapis do pliku (json): [...]")
        self.label_new_records = QLabel("Nowych zapisów: [...]")

        layout.addWidget(self.label_online_api)
        layout.addWidget(self.label_offline_read)
        layout.addWidget(self.label_offline_save)
        layout.addWidget(self.label_new_records)
        self.setLayout(layout)

    def refreshStatus(self, status: dict) -> None:
        """
        update the labels
        """
        # API
        if status["online_connection"]:
            self.label_online_api.setText("Połączenie z API: [OK]")
            self.label_online_api.setStyleSheet("color: green;")
        else:
            error_code = status["online_code"]
            self.label_online_api.setText(f"Połączenie z API: [BŁĄD] ({error_code})")
            self.label_online_api.setStyleSheet("color: red;")
            QMessageBox.critical(self, f"Błąd połączenia", f"Nie udało się połączyć z API ({error_code})")

        # READ FILE
        if status["offline_json"]:
            self.label_offline_read.setText("Odczyt pliku (json): [OK]")
            self.label_offline_read.setStyleSheet("color: green;")
        else:
            self.label_offline_read.setText("Odczyt pliku (json): [BŁĄD]")
            self.label_offline_read.setStyleSheet("color: red;")

        # SAVE FILE
        if status["save_json"]:
            self.label_offline_save.setText("Zapis do pliku (json): [OK]")
            self.label_offline_save.setStyleSheet("color: green;")
        else:
            self.label_offline_save.setText("Zapis do pliku (json): [BŁĄD]")
            self.label_offline_save.setStyleSheet("color: red;")

        # NEW RECORDS
        self.label_new_records.setText(f"Nowych zapisów: [{status['new_records']}]")
        if status["new_records"] == 0 and status["online_connection"]: 
            QMessageBox.information(self, "Dane aktualne", "Nie znaleziono nowych danych.")


class SearchStation(QComboBox):
    """
    Dropdown filter limiting records shown to 1 city; \n
    Used for FiltersPanel & charts tab\n
    Needs a list made by backend.getUniqueStations
    """
    def __init__(self,stations_list:list[str]) -> None:
        super().__init__()
        self.addItem("-")
        self.addItems(stations_list)

# TODO SHALL WE PASS VALUES AS MONDAY, TUESDAY??
class SelectWeekday(QComboBox):
    """
    Dropdown filter limiting records shown to 1 weekday; \n
    Used for FiltersPanel\n
    """

    # 
    def __init__(self) -> None:
        super().__init__()
        self.addItem("-")
        self.addItem("Poniedziałek",1)
        self.addItem("Wtorek",2)
        self.addItem("Środa",3)
        self.addItem("Czwartek",4)
        self.addItem("Piątek",5)
        self.addItem("Sobota",6)
        self.addItem("Niedziela",0)


class CalendarMode(QWidget):
    """
    3 horizontal QRadioButtons for changing behavior of calendars in FiltersPanel
    """
    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout()

        self.none = QRadioButton("Bez dat")
        self.day = QRadioButton("Dzień")
        self.range = QRadioButton("Zakres")
        self.weekday = QRadioButton("Dzień tyg.")

        self.day.setChecked(True) # default to day

        layout.addWidget(self.none)
        layout.addWidget(self.day)
        layout.addWidget(self.range)
        layout.addWidget(self.weekday)
        self.setLayout(layout)

class ColumnFilters(QComboBox):
    """
    Dropdown filter for showing only 1 parameter (eg. temperature / pressure)
    Used both for FiltersPanel & charts tab
    """
    def __init__(self) -> None:
        super().__init__()
        self.addItem("-", "")
        self.addItem("Temperatura", "temperatura")
        self.addItem("Prędkość wiatru", "predkosc_wiatru")
        self.addItem("Wilgotność", "wilgotnosc_wzgledna")
        self.addItem("Suma opadu", "suma_opadu")
        self.addItem("Ciśnienie", "cisnienie")

class FiltersRange(QWidget):
    """
    2 QDoubleimit choosen parameter (column) range to <left;right>
    """
    def __init__(self) -> None:
        super().__init__() 
        layout = QHBoxLayout()

        self.minimum = QDoubleSpinBox()
        self.maximum = QDoubleSpinBox()

        self.minimum.setRange(-100, 2000)
        self.maximum.setRange(-100, 2000)

        layout.addWidget(self.minimum)
        layout.addWidget(self.maximum)
        self.setLayout(layout)

class FiltersPanel(QGroupBox):
    """
    A great contraption taking care of everything Filter-related in the main tab\n
    Emits dict sitgnal with filters, ready for backend to process
    """
    filtersUpdated = pyqtSignal(dict)
    def __init__(self,stations_list) -> None:
        super().__init__()
        layout = QVBoxLayout()


        self.station_selected = SearchStation(stations_list)
        self.week_day = SelectWeekday()
        self.calendar_mode = CalendarMode()
        self.calendar_start = QCalendarWidget()
        self.calendar_end = QCalendarWidget()
        self.filter_type = ColumnFilters()
        self.range_widget = FiltersRange()
        

        self.update_button = QPushButton("Aktualizuj filtry")
        self.update_button.clicked.connect(self.updateFilters)
        # managing calendars toggling any of QRadioButtons
        self.calendar_mode.none.toggled.connect(self.calendarsGreyOut)
        self.calendar_mode.day.toggled.connect(self.calendarsGreyOut)
        self.calendar_mode.range.toggled.connect(self.calendarsGreyOut)

        layout.addWidget(self.station_selected)
        layout.addWidget(self.calendar_mode)
        layout.addWidget(self.week_day)
        layout.addWidget(self.calendar_start)
        layout.addWidget(self.calendar_end)
        layout.addWidget(QLabel("Wielkość fizyczna; Zakres"))
        layout.addWidget(self.filter_type)
        layout.addWidget(self.range_widget)
        layout.addWidget(self.update_button)    
        self.setLayout(layout)

        self.calendarsGreyOut()


    
    def calendarsGreyOut(self) -> None:
        """Greying out calendars or weekday, depending on QRadioButton choosen"""
        is_none = self.calendar_mode.none.isChecked()
        is_day = self.calendar_mode.day.isChecked()
        is_range = self.calendar_mode.range.isChecked()
        is_weekday = self.calendar_mode.weekday.isChecked()

        if is_none:
            self.week_day.setEnabled(False)
            self.calendar_start.setEnabled(False)
            self.calendar_end.setEnabled(False)
        if is_day:
            self.week_day.setEnabled(False)
            self.calendar_start.setEnabled(True)
            self.calendar_end.setEnabled(False)
        if is_range:
            self.week_day.setEnabled(False)
            self.calendar_start.setEnabled(True)
            self.calendar_end.setEnabled(True)
        if is_weekday:
            self.week_day.setEnabled(True)
            self.calendar_start.setEnabled(False)
            self.calendar_end.setEnabled(False)
            
    def updateFilters(self) -> None: 
        """Collect all elements into a dict with filter, emit signal"""
        date_start: str = ""
        date_end: str = ""

        # Get the right date from the right calendar
        if self.calendar_mode.day.isChecked() or self.calendar_mode.range.isChecked():
            date_start: str = self.calendar_start.selectedDate().toString("yyyy-MM-dd")
    
        if self.calendar_mode.range.isChecked():
            date_end: str = self.calendar_end.selectedDate().toString("yyyy-MM-dd")

        filters = {
            "station": self.station_selected.currentText() if self.station_selected.currentText() != "-" else "",
            "filter_type": self.filter_type.currentData(),
            "date_start": date_start,
            "date_end": date_end,
            "min_val": self.range_widget.minimum.value(),
            "max_val": self.range_widget.maximum.value(),
            "weekday": self.week_day.currentData()
        }

        self.filtersUpdated.emit(filters)

class Chart(FigureCanvasQTAgg):
    """The main chart in charts tab, pretty much empty"""
    def __init__(self, figure=None) -> None:
        super().__init__(figure)

class App(QMainWindow):
    """
    The mighty APP - displaying evertyhing, communicating with .backend functions, keeping it all together
    # Behold the mightness(madness) of my creation!
    """

    def __init__(self) -> None:
        super().__init__()
        
        # backend-related
        self.data_json = DataJson()
        self.sql = SqlDataFilters(self.data_json.data)
        self.filters = {}
        self.stations: list[str] = self.sql.getUniqueStations()

        # Table contents to be displayed
        self.shown_all = self.sql.filterForMain(**self.filters)
        self.shown_avgs = self.sql.getAllStatistics(**self.filters)

        # main-tab related
        self.download_button = DownloadButton(self.data_json)
        self.filters_panel: FiltersPanel = FiltersPanel(self.stations)
        self.display_status = DisplayStatus()
        self.main_table = MainWeatherTable()
        self.statistics_table = StatisticsTable()

        # charts-tab related
        self.station_choice_charts = SearchStation(self.stations)
        self.column_choice_charts = ColumnFilters()
        self.station_choice_charts.currentIndexChanged.connect(self.updateChart)
        self.column_choice_charts.currentIndexChanged.connect(self.updateChart)
        self.shown_figure = Figure()
        self.canvas_charts = Chart(self.shown_figure)

        self.setupGuiLooks()

        # Initial table display
        self.main_table.displayData(self.shown_all)
        self.statistics_table.displayData(self.shown_avgs)
        self.handleDataUpdate(self.data_json.status)
        self.updateChart()

        # Managing any of the buttons clicked
        self.download_button.statusUpdated.connect(self.handleDataUpdate)
        self.filters_panel.filtersUpdated.connect(self.handleFiltersUpdate)

    def setupGuiLooks(self) -> None:
        """
        APP GUI SETUP - ONLY THE LOOKING PART; NO THINKING
        Every tab, every Widged structured to look how it looks
        """
        self.setWindowTitle("IMGW pogoda - Jakub Hościło")
        self.setMinimumSize(1400,850)
        self.resize(1400,850)

        # 3 "main" layouts - for main (tables) tab, charts and 1 to use as central
        layout_MAIN = QVBoxLayout()
        layout_tables = QHBoxLayout()
        layout_charts = QVBoxLayout()

        # Filling up the layout_tables (broken down to left & right)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.download_button)
        left_layout.addWidget(self.filters_panel)
        left_layout.addWidget(self.display_status)
        
        left_layout.addStretch()
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.main_table,4)
        right_layout.addWidget(self.statistics_table,1)

        layout_tables.addLayout(left_layout, 1)
        layout_tables.addLayout(right_layout, 4)

        # Filing up the layout_charts (broken down to layout_charts_choice & canvas_charts)
        layout_charts_choice = QHBoxLayout()
        layout_charts_choice.addWidget(self.station_choice_charts)
        layout_charts_choice.addWidget(self.column_choice_charts)

        layout_charts.addLayout(layout_charts_choice)
        layout_charts.addWidget(self.canvas_charts)

        # Creating 2 tabs - Tabela (layout_tables) & Wykresy (layout_charts) 
        tabs = QTabWidget()

        tab1 = QWidget()
        tab1.setLayout(layout_tables)
        tab2 = QWidget()
        tab2.setLayout(layout_charts)
        self.setup_info_tab()

        tabs.addTab(tab1,"Tabela")
        tabs.addTab(tab2,"Wykresy")
        tabs.addTab(self.info_tab,"Informacje")
        

        layout_MAIN.addWidget(tabs)

        # Setting up central_widget - main window of the app
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(layout_MAIN)

    def handleDataUpdate(self,status:dict) -> None:
        """
        Method used by DownloadButton to refresh status display 
        If database (.json) has changed (new records found) - update .db, refresh tables
        """
        self.display_status.refreshStatus(status)

        if status["new_records"]:
            self.sql.fillDbWithData()
            self.updateTables(**self.filters)
    
    def handleFiltersUpdate(self,filters:dict) -> None:
        """
        Method used with FiltersUpdate dict signal emitted to update tables with new, filtered results
        """
        self.filters = filters
        self.updateTables()

    def updateTables(self) -> None: 
        """
        Refresh shown_all & shown_avgs using new filters, refresh tables with filters applied\n
        Also used to display newly dowloaded data, since filters don't change
        """
        self.shown_all = self.sql.filterForMain(**self.filters)
        self.shown_avgs = self.sql.getAllStatistics(**self.filters)

        self.main_table.displayData(self.shown_all)
        self.statistics_table.displayData(self.shown_avgs)
            
    def updateChart(self) -> None:
        """
        Entire logic behind the charts tab - if any of the QComboBoxes are changed, Asks db for dates, values, puts them as X,Y into the chart 
        """

        # Don't do anything if either station/column is not choosen
        station: str = self.station_choice_charts.currentText()
        column = self.column_choice_charts.currentData()
        if not column or not station: return

        self.column_names: dict[str, str] = {
            "temperatura": "Temperatura",
            "predkosc_wiatru": "Prędkość wiatru",
            "wilgotnosc_wzgledna": "Wilgotność",
            "suma_opadu": "Suma opadu",
            "cisnienie": "Ciśnienie"
        }
        
        # Ask db for data
        data = self.sql.getDataForChart(station,column)
        if not data: return

        # Convert data into matplotlib-drawable lists
        x: list[str] = [f"{row['data_pomiaru']} {row['godzina_pomiaru']}:00" for row in data]
        y = [row[column] for row in data]

        # Draw
        self.shown_figure.clear()
        ax: Axes = self.shown_figure.add_subplot()
        ax.plot(x,y,marker="o")

        # Formatting the plot - Title, grid
        ax.set_title(f"{self.column_names[column]} dla stacji {station}")
        ax.grid(True, linestyle='--', alpha=0.7)
        # Format the X-axis - with many db records it becomes crowded
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15))
        self.shown_figure.autofmt_xdate()

        self.canvas_charts.draw()

    def setup_info_tab(self):
        self.info_tab = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel()
        info_label.setWordWrap(True) # Zawijanie tekstu
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_text = """
        <h2>Informacje o projekcie</h2>
        <p>Projekt powstał w ramach przedmiotu Informatyka na Politechnice Gdańskiej, realizowanego w ramach studiów pierwszego stopnia na kierunku Automatyka, Robotyka i Systemy Sterowania. Autorem projektu jest Jakub Hościło.</p>
        <p>Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej –
        Państwowy Instytut Badawczy.<br>
        Dane Instytutu
        Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały
        przetworzone.</p>
        """
        
        info_label.setText(info_text)
        info_label.setOpenExternalLinks(True)

        layout.addWidget(info_label)
        self.info_tab.setLayout(layout)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    app.exec()
