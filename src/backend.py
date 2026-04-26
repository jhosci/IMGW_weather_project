import requests
import json
import sqlite3

# some of the records (like cisnienie on Kasprowy Wierch) are "null" values, json lib already converts it to None, but still keep that in mind for maths

def __doWeHaveAFolder() -> tuple[str,str]: 
    """
    checks/creates ./data where .json & .db will be stored; makes filepaths Win/macOS/Linux proof (at least I hope so)\n
    returns filepaths for .json &.db
    """
    import os

    dir = "data"
    if not os.path.exists(dir): os.mkdir(dir)

    json = os.path.join(dir, "weather_history.json")
    db = os.path.join(dir, "weather_history.db")
    
    return json, db

url_api = "https://danepubliczne.imgw.pl/api/data/synop"
# url_api = "http://google.com/404" # testing
json_file_path,db_file_path = __doWeHaveAFolder()

class DataJson():
    """
    Everything data-storing related - downloads, reads, saves ()
    .data and .status are the important ones. Also .updateAll() for read/download/save
    """
    def __init__(self,url:str=url_api,filepath:str=json_file_path) -> None:
        self.url = url
        self.filepath = filepath

        self.data = []

        self.status = {"offline_json":True, "online_connection":True,"online_code":None, "save_json":True, "new_records":0}
        self.updateAll()
        

    def updateAll(self) -> None: 
        """
        The most important func here - does all the reading/downloading/saving into self.data and keeps self.status updated
        """
        self.status = {"offline_json":True, "online_connection":True,"online_code":None, "save_json":True, "new_records":0}
        self.data = self.__jsonRead()

        # new_records are updated inside __mergeData, not updateAll - to avoid passing new_records count

        if not self.data: 
            self.status["offline_json"] = False
        
        online_attempt_result, new_data = self.__downloadData()
        self.status["online_code"] = online_attempt_result
        if online_attempt_result != "200":
            self.status["online_connection"] = False
        
        new_data = self.__convertTypes(new_data)

        self.data = self.__mergeData(new_data)

        save_attempt_result = self.__jsonWrite()
        if save_attempt_result != 0:
            self.status["save_json"] = False
        


    def __convertTypes(self, data:list[dict]) -> list[dict]:
        """
        Changes json default strings to int, float types where necessary
        """
        scheme = {'id_stacji':"int", 'stacja':"str", 'data_pomiaru':"str", 'godzina_pomiaru':"int", 'temperatura':"float", 'predkosc_wiatru':"float", 'kierunek_wiatru':"float", 'wilgotnosc_wzgledna':"float", 'suma_opadu':"float", 'cisnienie':"float"}
        try:
            for record in data:
                for key,val in record.items(): 
                    if val != None:
                        match scheme[key]:
                            case "int": record[key] = int(val)
                            case "float": record[key] = float(val)
                            case "str": record[key] = str(val)
            return data
        except: return []


    def __mergeData(self, new:list[dict]) -> list[dict]: 
        """
        Adds new records to existing list database, returns said database
        """

        existing = {(record.get("id_stacji"),record.get("data_pomiaru"),record.get("godzina_pomiaru")) for record in self.data}
        
        new_records = 0 
        for record in new:
            key = (record.get("id_stacji"),record.get("data_pomiaru"),record.get("godzina_pomiaru"))

            if key not in existing:
                self.data.append(record)
                existing.add(key)
                new_records += 1
        
        self.status["new_records"] = new_records
        return self.data
    
    
    def __downloadData(self) -> tuple[str,list[dict]]:
        """
        Connects to API, returns tuple of (statuscode(or error message if no connection established), list of downloaded data in standarized list (or [] on errors)
        """
        try:
            answer = requests.get(self.url,timeout=5) # change if you wanna see timeout

            if answer.status_code != 200 :
                return str(answer.status_code),[] #returns error code + empty list if connected with errors
            else: return str(answer.status_code), answer.json()


        #returns these + empty list if not connected
        except requests.exceptions.ConnectionError:
            return "Connection Error",[]
        except requests.exceptions.Timeout:
            return "Timeout Error",[]
        except Exception as e:
            return "Unexpected Error: "+str(e),[]


    def __jsonRead(self) -> list[dict]:
        """
        Tries opening database file (.json), returns list or [] on errors
        """
        try:
            with open(self.filepath,"r",encoding="utf-8") as file:
                data = json.load(file)
                return data
        except: return []


    def __jsonWrite(self) -> int:
        """
        Writes the data into .json file (clears the file first), returns 0 if success, else 1
        """
        try:
            with open(self.filepath,"w",encoding="utf-8") as file:
                json.dump(self.data,file,ensure_ascii=False,indent=4)
                return 0
        except: return 1

class SqlDataFilters():
    """
    Everything SQL related - creating, updating, queries to the db
    Use fillDbWithData() with DataJson.data to add new records 
    """

    def __init__(self, json_data:list[dict], filepath:str=db_file_path) -> None:
        self.__filepath = filepath
        self.raw_data = json_data
        self.__createTable()

        self.fillDbWithData()


    def __createTable(self) -> None:
        """
        Create the db if doesn't exist yet
        """
        with sqlite3.connect(self.__filepath) as connection:
            cursor = connection.cursor()

            query = """
            CREATE TABLE IF NOT EXISTS Weather (
                id_stacji INTEGER,
                stacja TEXT,
                data_pomiaru TEXT,
                godzina_pomiaru INTEGER,
                temperatura REAL,
                predkosc_wiatru REAL,
                kierunek_wiatru REAL,
                wilgotnosc_wzgledna REAL,
                suma_opadu REAL,
                cisnienie REAL,
                PRIMARY KEY (id_stacji, data_pomiaru, godzina_pomiaru)
            );
            """

            cursor.execute(query)

            connection.commit()


    def fillDbWithData(self) -> None:
        """
        Update the db with new data from .json
        """
        with sqlite3.connect(self.__filepath) as connection:
            cursor = connection.cursor()

            query = """INSERT OR IGNORE INTO Weather (id_stacji, stacja, data_pomiaru, godzina_pomiaru, temperatura, predkosc_wiatru, kierunek_wiatru, wilgotnosc_wzgledna, suma_opadu, cisnienie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            data_to_be_added = [list(record.values()) for record in self.raw_data]
            cursor.executemany(query,data_to_be_added)

            connection.commit()

     
    def __theQueryingBehemoth(
            self, 
            query, 
            station:str="", 
            filter_type:str="", 
            date_start:str="", 
            date_end:str="", 
            min_val:float=0, 
            max_val:float=0,
            ending:str="",
            weekday:int|None=None
            ) -> list[dict]:
        """
        Query is a valid SQL question starting with 'SELECT'; ending 'FROM Weather WHERE 1=1' so rest can be added with AND\n
        Filter: "temperatura" | "predkosc_wiatru" | "kierunek_wiatru" | "wilgotnosc_wzgledna" | "suma_opadu" | "cisnienie")\n
        Dates are "YYYY-MM-DD"; use date_start for one date or both for range\n
        Weekday: 0 for Sunday as 1st weekday\n
        ## One Query to rule them all, One Query to find them, One Query to bring them all, and in the darkness bind them - or was it the ring?
        """
        
        """
        A truly arcane and bewildering method, whereby I need not trouble myself over which parameter ought to come first, but may instead append them all as "AND..." in most sorcerous succesion
        """
        parameters = []
        if station: 
            query += " AND stacja = ?"
            parameters.append(station)

        if filter_type: 
            query += f" AND {filter_type} BETWEEN ? AND ?"
            parameters.append(min_val)
            parameters.append(max_val)

        if date_end: 
            query += " AND data_pomiaru BETWEEN ? AND ?"
            parameters.append(date_start)
            parameters.append(date_end)
        elif date_start:
            query += " AND data_pomiaru = ?"
            parameters.append(date_start) 
        elif weekday is not None:
            query += " AND CAST(strftime('%w', data_pomiaru) AS INTEGER) = ?"
            parameters.append(weekday)
        

        # useful for GROUP BY, ORDER BY, LIMIT and all the clauses after WHERE
        if ending:
            query += ending

        with sqlite3.connect(self.__filepath) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(query,parameters)

            result = [dict(record) for record in cursor.fetchall()]
            return result


    def filterForMain(self,             
            station:str="", 
            filter_type:str="", 
            date_start:str="", 
            date_end:str="", 
            min_val:float=0, 
            max_val:float=0,
            weekday:int|None=None
            ) -> list[dict]: 
        """
        For the main table\n
        Func to find all records with any and all filters applied\n
        Filter: "temperatura" | "predkosc_wiatru" | "kierunek_wiatru" | "wilgotnosc_wzgledna" | "suma_opadu" | "cisnienie")\n
        Dates are "YYYY-MM-DD"; use date_start for one date or both for a range between\n
        Weekday: 0 for Sunday as 1st weekday\n
        """
        # I just don't want to type all the arguments again, instead pack them into dict and unpack as Behemoths args
        arguments = locals() 
        arguments.pop("self") 


        query = "SELECT * FROM Weather WHERE 1=1"
        return self.__theQueryingBehemoth(query,**arguments)

    def _getStatistics(
            self, 
            analyze_column:str="",
            station:str="", 
            filter_type:str="", 
            date_start:str="", 
            date_end:str="", 
            min_val:float=0, 
            max_val:float=0,
            weekday:int|None=None
            ) -> list[dict]: 
        """
        Func to find mean, min, max, min_station, max_station with any and all filters applied, BUT for one column (eg. cisnienie)\n
        Filter & analyze_column: "temperatura" | "predkosc_wiatru" | "kierunek_wiatru" | "wilgotnosc_wzgledna" | "suma_opadu" | "cisnienie")\n
        Dates are "YYYY-MM-DD"; use date_start for one date or both for a range between\n
        Weekday: 0 for Sunday as 1st weekday\n
        RETURNS {AVG, MIN, MIN_STATION, MAX, MAX_sTATION}
        """
        # I just don't want to type all the arguments again, instead pack them into dict and unpack as Behemoths args
        arguments = locals()
        arguments.pop("self")
        arguments.pop("analyze_column")
        
        # query for AVG, MIN, MAX values
        query = f"""SELECT ROUND(AVG({analyze_column}),2) as avg, MIN({analyze_column}) as min, MAX({analyze_column}) as max FROM Weather WHERE 1=1"""
        result = self.__theQueryingBehemoth(query,**arguments)

        # query for station with MIN value
        query = f"""SELECT stacja FROM Weather WHERE 1=1"""
        ending = f"""
        AND {analyze_column} IS NOT NULL
        ORDER BY {analyze_column} ASC
        LIMIT 1
        """
        result_min = self.__theQueryingBehemoth(query,**arguments,ending=ending)

        # query for station with MAX value
        query = f"""SELECT stacja FROM Weather WHERE 1=1"""
        ending = f"""
        AND {analyze_column} IS NOT NULL
        ORDER BY {analyze_column} DESC
        LIMIT 1
        """
        result_max = self.__theQueryingBehemoth(query,**arguments,ending=ending)

        # Connect the queries into one result
        if not result_min or not result_max: return [{"avg": 0, "min": 0, "max": 0, "min_station": "-", "max_station": "-"}]

        station_lowest = result_min[0]["stacja"]
        station_highest = result_max[0]["stacja"]
        result[0]["min_station"] = station_lowest
        result[0]["max_station"] = station_highest

        return result

    def getAllStatistics(
                self, 
                station:str="", 
                filter_type:str="", 
                date_start:str="", 
                date_end:str="", 
                min_val:float=0, 
                max_val:float=0,
                weekday:int|None=None
                ) -> list[dict]: 
            """
            For the statistics table\n
            Func to find mean, min, max, min_station, max_station with any and all filters applied, for EVERY column\n
            Filter: "temperatura" | "predkosc_wiatru" | "kierunek_wiatru" | "wilgotnosc_wzgledna" | "suma_opadu" | "cisnienie")\n
            Dates are "YYYY-MM-DD"; use date_start for one date or both for a range between\n
            Weekday: 0 for Sunday as 1st weekday\n
            RETURNS [{AVG, MIN, MIN_STATION, MAX, MAX_STATION}*n]
            """
            arguments = locals()
            arguments.pop("self")

            analyze_columns = ["temperatura", "predkosc_wiatru", "kierunek_wiatru", "wilgotnosc_wzgledna", "suma_opadu", "cisnienie"]    
            column_names = {"temperatura":"Temperatura", "predkosc_wiatru":"Prędkość wiatru", "kierunek_wiatru":"Kierunek wiatru", "wilgotnosc_wzgledna":"Wilgotność względna", "suma_opadu":"Suma opadu", "cisnienie":"Ciśnienie"}        
            
            # It just calls _getStatistics() analyze_columns times in a loop
            all_results = []
            for column in analyze_columns:
                result = self._getStatistics(analyze_column=column, **arguments)
                
                if result:
                    row = result[0]

                    row["analyzed_column"] = column_names[column]
                    all_results.append(row)
                    
            return all_results
    
    def getUniqueStations(self) -> list[str]:
        """Func to find unique station names, for dropdown menu in FiltersPanel"""
        query = "SELECT DISTINCT stacja FROM Weather ORDER BY stacja ASC"
        with sqlite3.connect(self.__filepath) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]
        
    def getDataForChart(self,station:str="",analyzed_column:str="") -> list[dict]:
        """
        Func to fetch data needed for chart\n
        analyzed_column: "temperatura" | "predkosc_wiatru" | "kierunek_wiatru" | "wilgotnosc_wzgledna" | "suma_opadu" | "cisnienie")
        """

        query = f"""SELECT data_pomiaru, godzina_pomiaru, {analyzed_column} FROM Weather WHERE 1=1"""
        ending = "ORDER BY data_pomiaru ASC, godzina_pomiaru ASC"
        return self.__theQueryingBehemoth(query,station=station,ending=ending)


""" This is how 1 record from the API looks like
    {
        "id_stacji": "12650",
        "stacja": "Kasprowy Wierch",
        "data_pomiaru": "2026-03-23",
        "godzina_pomiaru": "19",
        "temperatura": "-3.5",
        "predkosc_wiatru": "4",
        "kierunek_wiatru": "10",
        "wilgotnosc_wzgledna": "79.6",
        "suma_opadu": "0.01",
        "cisnienie": null # but usually float
    },
"""
if __name__ == "__main__":
    import time

    t1 = time.perf_counter_ns()


    db_json = DataJson(url_api,json_file_path)
    update = db_json.status
    print(update, len(db_json.data), " records total")


    db_sql = SqlDataFilters(db_json.data, db_file_path)


    t2 = time.perf_counter_ns()
    print(f"took me {(t2-t1)/1000000000} s")

