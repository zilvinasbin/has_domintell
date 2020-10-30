# has_domintell
Domintell modules for Home Assistant

Basic Home Assistant modules mapped to domintell devices

# Installation
Copy contents of the *custom_components* folder to your home assistants' */config/custom_components*

# Configuration

Configure connection to DETH02 module in your __configuration.yaml__

    # DOMINTEL
    domintell:
      host: !secret deth02_host
      password: !secret deth02_pass

## Configure lights

    # LIGHTS and LAMPS
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

### Parameters

* __type: BIR__ - Ordinary light using domintell DBIR modules 
* __type: DIM__ - Dimmer using Domintell DDIM modules
* __module__ -  domintell module ID, can be found printed on module, or through domintell configuration app
* __channel: 1, 2, 3__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __location__ - Location of a sensor, output (Currently Not used for Home Assistant)

*__Note:__ use __type:TRP__ for trip switch* 

## Binary sensors & buttons

    #Domintell buttons and sensors
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

    - platform: domintell
      devices:
        - type: TE1   
          module: 898
          channel: 1
          name: Bedroom T°
          force_update: true
          location: Home|Second floor|Bedroom

### Parameters

* __type: TE1__ - Module TE1
* __module__ -  domintell module ID, can be found printed on module, or through domintell configuration app
* __channel: 1, 2, 3__ - Output number of Dimintell module (depends on how many output module has)
* __name__ - Friendly name (will be visible in Home Assistant)
* __location__ - Location of a sensor, output (Currently Not used for Home Assistant)

# Dependencies
This module depends on python-domintell

More info at https://pypi.org/project/python-domintell/


# Supported HAS devices
* light
* switch
* climate
* binary sensor

# Supported Home Assistant versions
* 0.117.0 (https://www.home-assistant.io/blog/2020/10/28/release-117/)
* 0.116