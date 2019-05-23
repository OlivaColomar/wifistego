# wifistego
Wifistego is a tool developed to transmit hidden messages using the Wi-Fi frequency channels in the 2.4GHz band.

## Compatibility

### Emitter
* Linux
### Receiver
* Windows 10
## Dependencies

### Emitter

* create_ap
* hostapd

## Usage

### Send Information
```
python sendExf.py <ssid> <fileWithInfoToExfiltrate.txt>
```
### Receive Information
```
python recvExf.py <ssid>
```
