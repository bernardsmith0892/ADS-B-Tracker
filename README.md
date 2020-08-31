# ADS-B Tracker
 Simple program to decode ADS-B signals from an RTLSDR and track aircraft.
 
The foundational code comes from UC Berkeley's EE123 Lab 2, namely the main three functions that reads data from the RTLSDR (`main`, `signal_process`, and `sdr_read`) and the clever way to perform Manchester decoding (` bits = chunk[16::2] > signal[17::2] `). But the code to detect ADS-B preambles, decode the signal, and the classes to process packets and objects are mine.

Example:
```
[1598868525.1129477] Long DF17 ICAO: abde34 typecode: 29 MSG:8dabde34ea1f58868f3c08056c88
[1598868526.0508988] Short DF11 ICAO: abde34 typecode: None MSG:5dabde34835935
[1598868526.053882] Short DF23 ICAO: None typecode: None MSG:bb57bc6906b26a
As of 31/Aug/2020 00:08:48...

╔══════╦════════╦═════════╦═════════╦════════╦════════╦═══════╦═════╗
║ ICAO ║Callsign║Latitude ║Longitude║Altitude║Velocity║Heading║ Age ║
╠══════╬════════╬═════════╬═════════╬════════╬════════╬═══════╬═════╣
║abde34║FDX77___║21.22485 ║-157.9546║5725    ║292     ║242.3  ║2    ║
╚══════╩════════╩═════════╩═════════╩════════╩════════╩═══════╩═════╝
```