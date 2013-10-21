import os
import datetime
import logging

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("flightaware.client")

BASE_URL = "http://flightxml.flightaware.com/json/FlightXML2/"
MAX_RECORD_LENGTH = 15
EPOCH = datetime.datetime(1970, 1, 1)


def to_unix_timestamp(val):
    if val:
        if not isinstance(val, datetime.datetime):
            raise ValueError("input must be of type datetime")
        output = int((val - EPOCH).total_seconds())
    else:
        # Just bypass
        output = None
    return output


def from_unix_timestamp(val):
    return datetime.datetime.fromtimestamp(val)


class TrafficFilter(object):
    """
    "ga" to show only general aviation traffic
    "airline" to only show airline traffic
    null/empty to show all traffic.
    """
    GA = "ga"
    AIRLINE = "airline"
    ALL = None


class AirlineInsightReportType(object):
    ALTERNATE_ROUTE_POPULARITY = 1              # Alternate route popularity with fares
    PERCENTAGE_SCHEDULED_ACTUALLY_FLOWN = 2     # Percentage of scheduled flights that are actually flown
    PASSENGER_LOAD_FACTOR_ACTUALLY_FLOWN = 3    # Passenger load factor of flights that are actually flown
    CARRIERS_BY_CARGO_WEIGHT = 4                # Carriers by most cargo weight


class Client(object):
    def __init__(self, username, api_key):
        self.auth = HTTPBasicAuth(username, api_key)
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _request(self, method, data=None):
        url = os.path.join(BASE_URL, method)
        logger.debug("POST\n%s\n%s\n", url, data)

        r = requests.post(url=url, data=data, auth=self.auth, headers=self.headers)
        result = r.json()
        final = result
        key = "{}Result".format(method)
        if key in result:
            final = result[key]
            if "data" in final:
                final = final["data"]
        return final

    def aircraft_type(self, aircraft_type):
        """
        Given an aircraft type string such as GALX, AircraftType returns information about that type,  comprising the
        manufacturer  (for instance, "IAI"), type (for instance, "Gulfstream G200"), and description (like "twin-jet").

        type	string	aircraft type ID
        """
        data = {"type": aircraft_type}
        return self._request("AircraftType", data)

    def airline_flight_info(self, fa_flight_id):
        """
        AirlineFlightInfo returns additional information about a commercial airline flight, such as gate, baggage claim,
        and meal service information. This information is currently only available for some carriers and flights. To
        obtain the faFlightID, you can use a function such as GetFlightID, FlightInfoEx, or InFlightInfo.

        faFlightID	string	unique identifier assigned by FlightAware for this flight (or use "ident@departureTime")

        """
        data = {"faFlightID": fa_flight_id}
        return self._request("AirlineFlightInfo", data)

    def airline_flight_schedules(self, start_date, end_date, origin=None, destination=None, airline=None, flight_number=None, how_many=MAX_RECORD_LENGTH, offset=0):
        """
        AirlineFlightSchedules returns flight schedules that have been published by airlines. These schedules are available
        for the recent past as well as up to one year into the future.

        Flights performed by airline codeshares are also returned in these results.

        startDate	int	timestamp of earliest flight departure to return, specified in integer seconds since 1970 (UNIX epoch time)
        endDate	int	timestamp of latest flight departure to return, specified in integer seconds since 1970 (UNIX epoch time)
        origin	string	optional airport code of origin. If blank or unspecified, then flights with any origin will be returned.
        destination	string	optional airport code of destination. If blank or unspecified, then flights with any destination will be returned.
        airline	string	optional airline code of the carrier. If blank or unspecified, then flights on any airline will be returned.
        flightno	string	optional flight number. If blank or unspecified, then any flight number will be returned.
        howMany	int	maximum number of past records to obtain. Must be a positive integer value less than or equal to 15, unless SetMaximumResultSize has been called.
        offset	int	must be an integer value of the offset row count you want the search to start at. Most requests should be 0 (most recent report).
        """
        data = {
            "startDate": to_unix_timestamp(start_date),
            "endDate": to_unix_timestamp(end_date),
            "origin": origin,
            "destination": destination,
            "airline": airline,
            "flightno": flight_number,
            "howMany": how_many,
            "offset": offset,
        }
        results = self._request("AirlineFlightSchedules", data)
        for item in results:
            item["departure_time"] = from_unix_timestamp(item["departuretime"])
            item["arrival_time"] = from_unix_timestamp(item["arrivaltime"])
        return results

    def airline_info(self, airline):
        """
        AirlineInfo returns information about a commercial airline/carrier given an ICAO airline code.

        airlineCode	string	the ICAO airline ID (e.g., COA, ASA, UAL, etc.)
        """
        data = {"airlineCode": airline}
        return self._request("AirlineInfo", data)

    def airline_insight(self, origin, destination, report_type=AirlineInsightReportType.PERCENTAGE_SCHEDULED_ACTUALLY_FLOWN):
        """
        AirlineInsight returns historical booking and airfare information that has been published by airlines. Currently this
        information is only available for airports located within the United States and its territories. Information is
        historical and is aggregated from the 12 months prior to the most recently published (generally 4 to 6 months delayed).
        The returned data may involve estimated or extrapolated amounts.

        This function can return one of several types of reports, as specified by the reportType argument:

        1 = Alternate route popularity with fares
        2 = Percentage of scheduled flights that are actually flown
        3 = Passenger load factor of flights that are actually flown
        4 = Carriers by most cargo weight


        origin	string	airport code of origin
        destination	string	airport code of destination
        reportType	int	type of report to obtain (see list of values above)

        """
        data = {
            "origin": origin,
            "destination": destination,
            "reportType": report_type,
        }
        return self._request("AirlineInsight", data)

    def airport_info(self, airport):
        """
        AirportInfo returns information about an airport given an ICAO airport code such as KLAX, KSFO, KORD, KIAH, O07, etc.
        Data returned includes name (Houston Intercontinental Airport), location (typically city and state),
        latitude and longitude, and timezone (:America/Chicago).

        The returned timezone is specified in a format that is compatible with the official IANA zoneinfo database and
        can be used to convert the timestamps returned by all other functions into localtimes.
        Support for timestamp conversion using zoneinfo identifiers is available natively or through third-party libraries
        for most programming languages. In some cases, the leading colon (":") character may need to be removed
        from the timezone identifier in order for it to be recognized by some timezone libraries.

        airportCode	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)

        Sample results for BNA:
            {
                u'latitude': 36.1244722,
                u'timezone': u':America/Chicago',
                u'name': u'Nashville Intl',
                u'longitude': -86.6781944,
                u'location': u'Nashville, TN'
            }
        """
        data = {"airportCode": airport}
        return self._request("AirportInfo", data)

    def all_airlines(self):
        """
        AllAirlines returns the ICAO identifiers of all known commercial airlines/carriers.

        See AirlineInfo to retrieve additional information about any of the identifiers returned.
        """
        return self._request("AllAirlines")

    def all_airports(self):
        """
        AllAirports returns the ICAO identifiers of all known airports. For airports that do not have an ICAO identifier, the FAA LID identifier will be used.
        See AirportInfo to retrieve additional information about any of the identifiers returned.
        """
        return self._request("AllAirports")

    def block_indent_check(self, ident):
        """
        Given an aircraft identification, returns 1 if the aircraft is blocked from public tracking, 0 if it is not.
        ident	string	requested tail number
        """
        data = {"ident": ident}
        return self._request("BlockIdentCheck", data)

    def count_airport_operations(self, airport):
        """
        Given an airport, CountAirportOperations returns integer values on the number of aircraft scheduled or actually
        en route or departing from the airport. Scheduled arrival is a non-airborne flight that is scheduled to the airport in question.
        """
        data = {"airport": airport}
        return self._request("CountAirportOperations", data)

    def count_all_enroute_airline_operations(self):
        """
        CountAllEnrouteAirlineOperations returns an array of airlines and how many flights each currently has enroute.
        """
        return self._request("CountAllEnrouteAirlineOperations")

    def decode_flight_route(self):
        raise NotImplementedError

    def decode_route(self):
        raise NotImplementedError

    def arrived(self, airport, how_many=MAX_RECORD_LENGTH, filter=TrafficFilter.ALL, offset=0):
        """
        Arrived returns information about flights that have recently arrived for the specified airport and maximum number of
        flights to be returned. Flights are returned from most to least recent. Only flights that arrived within the last 24 hours are considered.

        Times returned are seconds since 1970 (UNIX epoch seconds).

        See also Departed, Enroute, and Scheduled for other airport tracking functionality.

        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        howMany	int	determines the number of results. Must be a positive integer value less than or equal to 15, unless SetMaximumResultSize has been called.
        filter	string	can be "ga" to show only general aviation traffic, "airline" to only show airline traffic, or null/empty to show all traffic.
        offset	int	must be an integer value of the offset row count you want the search to start at. Most requests should be 0.
        """
        raise NotImplementedError

    def departed(self, airport, how_many=MAX_RECORD_LENGTH, filter=TrafficFilter.ALL, offset=0):
        """
        Departed returns information about already departed flights for a specified airport and maximum number of
        flights to be returned. Departed flights are returned in order from most recently to least recently departed.
        Only flights that have departed within the last 24 hours are considered.

        Times returned are seconds since 1970 (UNIX epoch seconds).

        See also Arrived, Enroute, and Scheduled for other airport tracking functionality.

        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        howMany	int	determines the number of results. Must be a positive integer value less than or equal to 15, unless SetMaximumResultSize has been called.
        filter	string	can be "ga" to show only general aviation traffic, "airline" to only show airline traffic, or null/empty to show all traffic.
        offset	int	must be an integer value of the offset row count you want the search to start at. Most requests should be 0.
        """
        raise NotImplementedError

    def enroute(self):
        raise NotImplementedError

    def fleet_arrived(self):
        raise NotImplementedError

    def fleet_scheduled(self):
        raise NotImplementedError

    def flight_info(self, ident, how_many=MAX_RECORD_LENGTH):
        """
        FlightInfo returns information about flights for a specific tail number (e.g., N12345), or ICAO airline code with flight number (e.g., SWA2558).

        The howMany argument specifies the maximum number of flights to be returned. Flight information will be returned from newest to oldest.
        The oldest flights searched by this function are about 2 weeks in the past.

        When specifying an airline with flight number, wither an ICAO or IATA code may be used to designate the airline, however andCodeshares and alternate idents are automatically searched.

        Times are in integer seconds since 1970 (UNIX epoch time), except for estimated time enroute, which is in hours and minutes.

        See FlightInfoEx for a more advanced interface.

        ident	string	requested tail number, or airline with flight number
        howMany	int	maximum number of past flights to obtain. Must be a positive integer value less than or equal to 15, unless SetMaximumResultSize has been called.
        """
        raise NotImplementedError

    def flight_info_ex(self):
        """
        FlightInfoEx returns information about flights for a specific tail number (e.g., N12345), or an ident (typically an ICAO airline with flight number, e.g., SWA2558),
        or a FlightAware-assigned unique flight identifier (e.g. faFlightID returned by another FlightXML function).

        The howMany argument specifies the maximum number of flights to be returned. When a tail number or ident is specified and multiple flights
        are available, the results will be returned from newest to oldest. The oldest flights searched by this function are about 2 weeks in the past.
        Codeshares and alternate idents are automatically searched. When a FlightAware-assigned unique flight identifier is supplied, at most a single result will be returned.

        Times are in integer seconds since 1970 (UNIX epoch time), except for estimated time enroute, which is in hours and minutes.

        See FlightInfo for a simpler interface.
        """
        raise NotImplementedError

    def get_flight_id(self, ident, departure_datetime):
        """
        GetFlightID looks up the "faFlightID" for a given ident and departure time. This value is a unique identifier assigned by
        FlightAware as a way to permanently identify a flight. The specified departure time must exactly match either the actual
        or scheduled departure time of the flight. The departureTime is specified as integer seconds since 1970 (UNIX epoch time).

        If more than one flight corresponds to the specified ident and departure time, then only the first matching faFlightID
        is returned. Codeshares and alternate idents are automatically searched.


        ident	string	requested tail number
        departureTime	int	time and date of the desired flight, UNIX epoch seconds since 1970
        """
        data = {
            "ident": ident,
            "departureTime": to_unix_timestamp(departure_datetime),
        }
        return self._request("GetFlightID", data)


    def get_historical_track(self):
        raise NotImplementedError

    def get_last_track(self):
        raise NotImplementedError

    def inbound_flight_info(self):
        raise NotImplementedError

    def in_flight_info(self):
        raise NotImplementedError

    def lat_lng_to_distance(self):
        raise NotImplementedError

    def lat_lng_to_heading(self):
        raise NotImplementedError

    def map_flight(self):
        raise NotImplementedError

    def map_flight_ex(self):
        raise NotImplementedError

    def metar(self, airport):
        """
        Given an airport, return the current raw METAR weather info. If no reports are available at the requested airport
        but are for a nearby airport, then the report from that airport may be returned instead.

        Use the MetarEx function for more functionality, including access to historical weather and parsed.
        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        """
        data = {"airport": airport}
        return self._request("Metar", data)

    def metar_ex(self, airport):
        """
        Given an airport, return the METAR weather info as parsed, human-readable, and raw formats. If no reports are available
        at the requested airport but are for a nearby airport, then the reports from that airport may be returned instead.
        If a value greater than 1 is specified for howMany then multiple past reports will be returned, in order of increasing
        age. Historical data is generally only available for the last 7 days.

        Use the Metar function for a simpler interface to access just the most recent raw report.
        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        """
        data = {"airport": airport}
        return self._request("MetarEx", data)

    def ntaf(self, airport):
        """
        Given an airport, return the terminal area forecast, if available.
        See Taf for a simpler interface.
        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        """
        data = {"airport": airport}
        return self._request("NTaf", data)

    def taf(self, airport):
        """
        Given an airport, return the terminal area forecast, if available.
        See NTaf for a more advanced interface.
        airport	string	the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        """
        data = {"airport": airport}
        return self._request("NTaf", data)

    def routes_between_airports(self):
        raise NotImplementedError

    def routes_between_airports_ex(self):
        raise NotImplementedError

    def scheduled(self):
        raise NotImplementedError

    def search(self):
        raise NotImplementedError

    def search_birdseye_in_flight(self):
        raise NotImplementedError

    def search_birdseye_positions(self):
        raise NotImplementedError

    def search_count(self):
        raise NotImplementedError

    def set_maximum_result_sizes(self):
        raise NotImplementedError

    def tail_owner(self, ident):
        """
        TailOwner returns information about an the owner of an aircraft, given a flight number or N-number. Data returned
        includes owner's name, location (typically city and state), and website, if any. Codeshares and alternate idents are automatically searched.

        ident	string	requested tail number
        """
        data = {"ident": ident}
        return self._request("TailOwner", data)

    def zipcode_info(self, zipcode):
        """
        ZipcodeInfo returns information about a five-digit zipcode. Of particular importance is latitude and longitude.

        zipcode	string	a five-digit U.S. Postal Service zipcode.
        """
        data = {"zipcode": zipcode}
        return self._request("ZipcodeInfo", data)

    def get_alerts(self):
        raise NotImplementedError

    def delete_alert(self):
        raise NotImplementedError

    def set_alert(self):
        raise NotImplementedError

    def register_alert_endpoint(self):
        raise NotImplementedError


