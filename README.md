# Warframe Prime Helper

Warframe Prime Helper is a tool that scans your screen for the prime parts selection screen and checks their prices.

![A screenshot of Warframe Prime Helper](https://i.imgur.com/8YHsmS8.png)

## Where can I get it?

- [Download the latest release for Windows](https://github.com/donaldsa18/WarframeTools/releases)

## Settings
![A screenshot of the preferences window](https://i.imgur.com/QQf3OFN.png)

### Crop Parameters
- Crop Parameters determines the dimensions of the window where primes show up. Change this if you are not using running Warframe at 1080p Windowed Mode

### Filter Parameters
- The filter parameters v1 and v2 describe the thresholds for a color to be considered part of text based on its value in HSV representation. You should only need to edit this if you have a screen saturation overlay or if Warframe changes their UI.
- The filter paramater delta describes how different the screen has to be from the last frame to be processed by the OCR engine. Reduce it if the program doesn't detect any primes.

### Updates
- The updates box manages price data from Warframe Market. Run Update Prices maybe once a week and run Update Ducats when new Primes are added to Warframe Market

### Rates
- The screencap slider determines how often the program checks your screen. It doesn't need to be any higher than 1, but you can increase it as much as performance allows.
- The Fissure slider determines how often the program checks the Warframe World State API for new fissure missions.
- The API threads slider determines how many connections are used to connect to the Warframe Market API. Please don't set it too high or their devs will get mad at me.

### Hide UI
- Hide elements of the UI with these checkboxes. Hide what you don't need to make the window smaller and less CPU intensive.

### Hide Relics
- Filter out relics you don't need.

### Hide Missions
- Hide mission types you don't like, like Mobile Defense for example.


## Building Guide
1. Download Python 3.6
2. Setup a virtual environment
`python -m venv env`
3. Activate the environment
`env\Scripts\activate.bat`
4. Install the dependencies
`pip install -r requirements.txt`
5. Run make.bat
`make.bat`
6. Now you should have an executable in target\Warframe Prime Helper\

Alternatively, you can run it in dev mode
`python main.py`
