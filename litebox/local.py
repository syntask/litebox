# MARK: - Imports
from PIL import Image, ImageDraw, ImageFont
import time
import os, sys
import requests

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(basedir)

# MARK: - Functions
def drawText(draw, text, font, fill, x, y, halign, valign):
    text_bbox = draw.textbbox((0, 0), text, font=font)
    textWidth = text_bbox[2] - text_bbox[0]
    textHeight = text_bbox[3] - text_bbox[1]
    if halign == 'center':
        x -= textWidth // 2
    elif halign == 'right':
        x -= textWidth
    if valign == 'center':
        y -= textHeight // 2
    elif valign == 'bottom':
        y -= textHeight
    draw.text((x, y), text, font=font, fill=fill)
    
def timeSplitFlap():
    # Adjustable variables
    timeSize = 85
    timeFont = ImageFont.truetype(basedir + '/assets/helvetica/Helvetica-Bold.ttf', timeSize)
    textColor = 255

    
    # Constants
    canvas_width = 250
    canvas_height = 122
    image = Image.new('1', (canvas_width, canvas_height), 0)
    draw = ImageDraw.Draw(image)
    
    # Computed variables
    hourStr = time.strftime('%I')
    minuteStr = time.strftime('%M')
    digitOne = hourStr[0]
    digitTwo = hourStr[1]
    digitThree = minuteStr[0]
    digitFour = minuteStr[1]
    
    drawText(draw, digitOne, timeFont, textColor, (canvas_width / 5) * 1 - 20, (canvas_height / 2) * 0.95, 'center', 'center')
    drawText(draw, digitTwo, timeFont, textColor, (canvas_width / 5) * 2 - 15, (canvas_height / 2) * 0.95, 'center', 'center')
    drawText(draw, ":", timeFont, textColor, (canvas_width / 2), (canvas_height / 2) * 0.65, 'center', 'center')
    drawText(draw, digitThree, timeFont, textColor, (canvas_width / 5) * 3 + 15, (canvas_height / 2) * 0.95, 'center', 'center')
    drawText(draw, digitFour, timeFont, textColor, (canvas_width / 5) * 4 + 20, (canvas_height / 2) * 0.95, 'center', 'center')
    draw.line([(0, canvas_height / 2), (canvas_width, canvas_height / 2)], fill=0, width=6)
    
    return image
    
def timePlain():
    # Adjustable variables
    timeSize = 85
    timeFont = ImageFont.truetype(basedir + '/assets/avigea.ttf', timeSize)
    textColor = 0
    dateSize = 16
    dateFont = ImageFont.truetype(basedir + '/assets/avigea.ttf', dateSize)
    
    # Constants
    canvas_width = 250
    canvas_height = 122
    image = Image.new('1', (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(image)
    
    # Computed variables
    timeStr = time.strftime('%I:%M').lstrip('0')
    dateStr = time.strftime('%A, %B %d %Y')
    
    timebbox = draw.textbbox((0, 0), timeStr, font=timeFont)
    
    drawText(draw, timeStr, timeFont, textColor, canvas_width / 2, canvas_height / 2 - 8, 'center', 'center')
    drawText(draw, dateStr, dateFont, textColor, canvas_width / 2, canvas_height / 2 + timebbox[3] / 2 + 8 - 8, 'center', 'top')
    
    
    return image
    
def timeMeridiem():
    # Adjustable variables
    timeSize = 85
    meridiemSize = 25
    timeFont = ImageFont.truetype(basedir + '/assets/avigea.ttf', timeSize)
    meridiemFont = ImageFont.truetype(basedir + '/assets/avigea.ttf', meridiemSize)
    meridiemPadding = 4
    textColor = 0
    
    # Constants
    canvas_width = 250
    canvas_height = 122
    image = Image.new('1', (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(image)
    
    # Computed variables
    timeStr = time.strftime('%I:%M').lstrip('0')
    meridiemStr = time.strftime('%p')
    timebbox = draw.textbbox((0, 0), timeStr, font=timeFont)
    meridiembbox = draw.textbbox((0, 0), meridiemStr, font=meridiemFont)
    
    drawText(draw, timeStr, timeFont, textColor, canvas_width / 2 - ((meridiembbox[2] + meridiemPadding) / 2), canvas_height / 2, 'center', 'center')
    
    drawText(draw, meridiemStr, meridiemFont, textColor, canvas_width / 2 + timebbox[2] / 2 + meridiemPadding / 2, canvas_height / 2 + timebbox[3] / 2, 'center', 'bottom')
    
    return image


def currentWeather():
    # Adjustable variables
    tempFont = ImageFont.truetype(basedir + '/assets/helvetica/helvetica.ttf', 42)
    conditionFont = ImageFont.truetype(basedir + '/assets/helvetica/helvetica.ttf', 12)
    windFont = ImageFont.truetype(basedir + '/assets/helvetica/helvetica.ttf', 12)
    textColor = 0
    # get weather from https://wttr.in/msp?format=j1
    
    # Constants
    canvas_width = 250
    canvas_height = 122
    image = Image.new('1', (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(image)
    weatherCodes = {
        "113": {"apiName": "Sunny", "icon": "clear-day"},
        "116": {"apiName": "Partly cloudy", "icon": "partly-cloudy-day"},
        "119": {"apiName": "Cloudy", "icon": "overcast"},
        "122": {"apiName": "Overcast", "icon": "overcast"},
        "143": {"apiName": "Mist", "icon": "fog"},
        "176": {"apiName": "Patchy rain possible", "icon": "rain"},
        "179": {"apiName": "Patchy snow possible", "icon": "snow"},
        "182": {"apiName": "Patchy sleet possible", "icon": "rain-snow-mix"},
        "185": {"apiName": "Patchy sleet possible", "icon": "rain-snow-mix"},
        "200": {"apiName": "Thundery outbreaks", "icon": "thunderstorm"},
        "227": {"apiName": "Blowing snow", "icon": "snow"},
        "230": {"apiName": "Blowing snow", "icon": "snow"},
        "248": {"apiName": "Fog", "icon": "fog"},
        "260": {"apiName": "Freezing fog", "icon": "fog"},
        "263": {"apiName": "Patchy light rain", "icon": "rain"},
        "266": {"apiName": "Light drizzle", "icon": "rain"},
        "284": {"apiName": "Heavy freezing drizzle", "icon": "rain-snow-mix"},
        "293": {"apiName": "Patchy light rain", "icon": "rain"},
        "296": {"apiName": "Light rain", "icon": "rain"},
        "299": {"apiName": "Moderate rain at times", "icon": "rain"},
        "302": {"apiName": "Moderate rain", "icon": "rain"},
        "305": {"apiName": "Heavy rain at times", "icon": "rain"},
        "308": {"apiName": "Heavy rain", "icon": "rain"},
        "311": {"apiName": "Light freezing rain", "icon": "rain-snow-mix"},
        "314": {"apiName": "Moderate or heavy freezing rain", "icon": "rain-snow-mix"},
        "317": {"apiName": "Light sleet", "icon": "rain-snow-mix"},
        "320": {"apiName": "Moderate or heavy sleet", "icon": "rain-snow-mix"},
        "323": {"apiName": "Patchy light snow", "icon": "snow"},
        "326": {"apiName": "Light snow", "icon": "snow"},
        "329": {"apiName": "Patchy moderate snow", "icon": "snow"},
        "332": {"apiName": "Moderate snow", "icon": "snow"},
        "335": {"apiName": "Patchy heavy snow", "icon": "snow"},
        "338": {"apiName": "Heavy snow", "icon": "snow"},
        "350": {"apiName": "Ice pellets", "icon": "rain-snow-mix"},
        "353": {"apiName": "Light rain shower", "icon": "rain"},
        "356": {"apiName": "Moderate or heavy rain shower", "icon": "rain"},
        "359": {"apiName": "Torrential rain shower", "icon": "rain"},
        "362": {"apiName": "Light sleet showers", "icon": "rain-snow-mix"},
        "365": {"apiName": "Moderate or heavy sleet showers", "icon": "rain-snow-mix"},
        "368": {"apiName": "Light snow showers", "icon": "snow"},
        "365": {"apiName": "Moderate or heavy sleet showers", "icon": "snow"},
        "335": {"apiName": "Patchy heavy snow", "icon": "snow"},
        "338": {"apiName": "Heavy snow", "icon": "snow"},
        "350": {"apiName": "Ice pellets", "icon": "rain-snow-mix"},
        "335": {"apiName": "Patchy heavy snow", "icon": "snow"},
        "338": {"apiName": "Heavy snow", "icon": "snow"},
        "332": {"apiName": "Moderate snow", "icon": "snow"},
        "329": {"apiName": "Patchy moderate snow", "icon": "snow"},
        "122": {"apiName": "Overcast", "icon": "overcast"},
        "119": {"apiName": "Cloudy", "icon": "overcast"},
        "116": {"apiName": "Partly cloudy", "icon": "partly-cloudy-day"},
        "113": {"apiName": "Sunny", "icon": "clear-day"},
        "143": {"apiName": "Mist", "icon": "fog"},
        "248": {"apiName": "Fog", "icon": "fog"},
        "386": {"apiName": "Patchy light rain with thunder", "icon": "thunderstorm"},
        "389": {"apiName": "Moderate or heavy rain with thunder", "icon": "thunderstorm"},
        "392": {"apiName": "Patchy light snow with thunder", "icon": "snow"},
        "395": {"apiName": "Moderate or heavy snow with thunder", "icon": "snow"}
    }
    
    # Computed variables
    weather = requests.get('https://wttr.in/msp?format=j1').json()
    print(weather)
    weatherCode = weather['current_condition'][0]['weatherCode']
    weatherDesc = weather['current_condition'][0]['weatherDesc'][0]['value']
    tempC = weather['current_condition'][0]['temp_C']
    tempF = weather['current_condition'][0]['temp_F']
    windKph = weather['current_condition'][0]['windspeedKmph']
    windMph = weather['current_condition'][0]['windspeedMiles']
    windKts = str(int(round(float(windMph) * 0.868976)))
    windDir = weather['current_condition'][0]['winddir16Point']
    windDeg = weather['current_condition'][0]['winddirDegree']
    icon = weatherCodes[weatherCode]['icon']
    
    # Insert the 100x100 weather icon here
    image.paste(Image.open(basedir + '/assets/weather-icons/' + icon + '.bmp'), (0, 20))
    
    drawText(draw, weatherDesc, conditionFont, textColor, 105, 41, 'left', 'center')
    drawText(draw, tempF + '°F', tempFont, textColor, 105, 69, 'left', 'center')
    drawText(draw, windKts + ' kts ' + windDir, windFont, textColor, 105, 99, 'left', 'center')
    
    topBarImage = topBar()
    image.paste(topBarImage, (0, 0))
    
    return image
    
def topBar():
    # Adjustable variables
    textSize = 11
    textFont = ImageFont.truetype(basedir + '/assets/helvetica/helvetica.ttf', textSize)
    textColor = 0
    
    # Constants
    canvas_width = 250
    canvas_height = 16
    image = Image.new('1', (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(image)
    
    drawText(draw, time.strftime('%A, %B %d %Y'), textFont, textColor, 3, 3, 'left', 'top')
    drawText(draw, time.strftime('%I:%M %p'), textFont, textColor, canvas_width - 3, 3, 'right', 'top')
    draw.line([(0, canvas_height - 1), (canvas_width, canvas_height - 1)], fill=0, width=1)
    
    return image


# MARK: - Main
image = currentWeather()
image.save('image.bmp')