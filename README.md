# ADS-B Tracker
 Simple program to decode ADS-B signals from an RTLSDR and track aircraft.
 
The foundational code comes from UC Berkeley's EE123 Lab 2, namely the main three functions that reads data from the RTLSDR (`main`, `signal_process`, and `sdr_read`) and the clever way to perform Manchester decoding (` bits = chunk[16::2] > signal[17::2] `). But the code to detect ADS-B preambles, decode the signal, and the classes to process packets and objects are mine.

Example:
```
$ python3.8 .\adsb_tracker.py
[1598916581.5571182] Long DF17 ICAO: aa75ef typecode: 4 MSG:8daa75ef25541332cf8c2080b14f
[1598916582.771031] Short DF11 ICAO: aa75ef typecode: None MSG:5daa75efd05edf
[1598916582.7750278] Short DF23 ICAO: None typecode: None MSG:bb54ebdfa0bdbe
[1598916582.8580236] Long DF17 ICAO: aa75ef typecode: 19 MSG:8daa75ef991079005828063b6635
As of 31/Aug/2020 13:29:43...

╔══════╦════════╦═════════╦═════════╦════════╦════════╦═══════╦═════╗
║ ICAO ║Callsign║Latitude ║Longitude║Altitude║Velocity║Heading║ Age ║
╠══════╬════════╬═════════╬═════════╬════════╬════════╬═══════╬═════╣
║a499c3║HAL1307_║21.32525 ║-157.9481║100     ║122     ║90.47  ║435  ║
║aa75ef║UAL2380_║21.32525 ║-157.9552║225     ║120     ║89.52  ║0    ║
║a2b677║        ║         ║         ║        ║        ║       ║208  ║
║adfbde║TEST1234║         ║         ║        ║        ║       ║439  ║
║000000║        ║         ║         ║        ║        ║       ║230  ║
║aa871b║        ║         ║         ║        ║        ║       ║85   ║
╚══════╩════════╩═════════╩═════════╩════════╩════════╩═══════╩═════╝
```