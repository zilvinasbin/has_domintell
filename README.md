# Domintell Smart Home integration custom component for Home Assistant (has_domintell)
Domintell modules for Home Assistant

Basic Home Assistant modules mapped to domintell devices

# Installation
1. Copy contents of the *custom_components* folder to your home assistants' */config/custom_components*
1. Configure component via configuration.yaml (see instructions below)
1. Restart home assistant

**Note:** You should not need to install python-domintell manually, it will be installed automatically

# Configuration

Configure connection to DETH02 module in your __configuration.yaml__

```
# DOMINTEL
domintell:
  host: deth02_host_ip:17481
  password: !secret deth02_pass
```

**Notes:** 
* Please specify UDP port for deth02 module. Default port is 17481. If port number is omited Serial connection will be used instead.
* If your DETH02 has no password set, put 'LOGIN' instead of password.
* It is absolutelly recomened to move host ip and passwords to secrets file!


## Configure lights

```
# LIGHTS and LAMPS
light:
  - platform: domintell
      devices:
      - type: BIR
        module: 1AE4       
        channel: 1
        name: My night lamp       
        location: Home|Second floor|My Room
      - type: BIR
        module: 1AE4       
        channel: 2
        name: Emmas bed light       
        location: Home|Second floor|My Room
      - type: DIM
        module:  ACF       
        channel: 1
        name: TV zone (dimmer)       
        location: Home|First floor|Main Room
      - type: DIM
        module:  ACF       
        channel: 2
        name: Kitchen       
        location: Home|First floor|Kitchen
```

### Parameters

* __type: BIR__ - Ordinary light using domintell DBIR modules 
* __type: DIM__ - Dimmer using Domintell DDIM modules
* __module__ -  domintell module ID (Hex), can be found printed on module, or through domintell configuration app. Please note that Domintell have changed Hex IDs to Decimal in their app. *You need to convert it back to Hex and use in this configuration.*
* __channel: 1, 2, 3__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __location__ - Location of a sensor, output (Currently Not used for Home Assistant)

*__Note:__ use __type:TRP__ for trip switch* 

## Binary sensors & buttons

```
#Domintell buttons and sensors
binary_sensor:     
  # IS4, IS8
  - platform: domintell
      devices:
      - type: IS8
        module: 247C
        channel: 1
        name: My button
        location: Home|First floor|Kitchen
      - type: IS8
        module: 247C
        channel: 2
        name: My sensor
        location: Home|First floor|Kitchen
```

### Parameters

* __type: IS8__ - Module type DISM08
* __type: IS4__ - Module type DISM04
* __type: BU1__ - Module type DPBU01
* __type: BU2__ - Module type DPBU02
* __type: BU4__ - Module type DPBU04
* __type: BU6__ - Module type DPBU06
* __module__ -  domintell module ID, can be found printed on module, or through domintell configuration app
* __channel: 1, 2, 3__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __location__ - Location of a sensor, output (Currently Not used for Home Assistant)


## Climate
```
climate:
  - platform: domintell
    devices:
      - type: TE1   
        module: 898
        channel: 1
        name: Bedroom T°
        force_update: true
        location: Home|Second floor|Bedroom
```
### Parameters

* __type: TE1__ - Module TE1
* __module__ -  domintell module ID, can be found printed on module, or through domintell configuration app
* __channel: 1, 2, 3__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __location__ - Location of a sensor, output (Currently Not used for Home Assistant)

## Switches
**Using DTRP01 Domintell module**

```
switch: 
  - platform: domintell
    devices:
      - type: TRP 
        module: 850
        channel: 1
        name: Parents room sockets
        path: Namas|2nd Floor|Master Bedroom
      - type: TRP
        module: 850
        channel: 2
        name: Parents TV
        path: Namas|2nd Floor|Master Bedroom
      - type: TRP
        module: 850
        channel: 3
        name: Bathroom sockets
        path: Namas|2nd Floor|Bathroom
      - type: TRP
        module: 850
        channel: 4
        name: Kids PC
        path: Namas|2nd Floor|Bedroom
```
### Parameters

* __type: TRP__ - Trip switch using Domintell DTRP01 module
* __module__ -  domintell module ID (Hex), can be found printed on module, or through domintell configuration app. Please note that Domintell have changed Hex IDs to Decimal in their app. *You need to convert it back to Hex and use in this configuration.*
* __channel: 1, 2, 3, 4__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __path__ - Location of a sensor, output (Currently Not used for Home Assistant)


# Dependencies
This module depends on python-domintell (ver 0.0.17)

More info at https://pypi.org/project/python-domintell/



# Supported HA devices
* light
* switch
* climate
* binary sensor
* binary variable VAR (binary only)

# Supported Home Assistant versions
* core-2023.6.1 ___(Running now)___ Modified to support Python 3.11

Not suported anymore:
* core-2021.4.6
* core-2021.1.5 
* 2020.12.7
* 0.118.0
* 0.117.0 (https://www.home-assistant.io/blog/2020/10/28/release-117/)
* 0.116