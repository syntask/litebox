#!/usr/bin/python
# -*- coding:utf-8 -*-

simMode = False

import sys
import os
basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(basedir)
import logging

if simMode:
    import tkinter as tk
    from PIL import ImageTk
else:
    from waveshare_epd import epd2in13_V4

import time
from PIL import Image, ImageDraw, ImageFont
import flask
import threading
import queue
import requests
import json

logging.basicConfig(level=logging.DEBUG)


# MARK: - Functions

def req(url, file, timeout):
    # url: URL to request
    # file: File name to save the cached response to
    # timeout: Time in seconds before the cache expires
    file = basedir + '/web_cache/' + file
    
    if os.path.exists(file):
        if time.time() - os.path.getmtime(file) < timeout * 60:
            with open(file, 'r') as f:
                text = f.read()
                return json.loads(text)
    response = requests.get(url)
    with open(file, 'w') as f:
        f.write(response.text)
    return response.json()

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
    timeFont = ImageFont.truetype(basedir + '/assets/fonts/helvetica_bold.ttf', timeSize)
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
    timeFont = ImageFont.truetype(basedir + '/assets/fonts/avigea.ttf', timeSize)
    textColor = 0
    dateSize = 16
    dateFont = ImageFont.truetype(basedir + '/assets/fonts/avigea.ttf', dateSize)
    
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
    timeFont = ImageFont.truetype(basedir + '/assets/fonts/avigea.ttf', timeSize)
    meridiemFont = ImageFont.truetype(basedir + '/assets/fonts/avigea.ttf', meridiemSize)
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
    tempFont = ImageFont.truetype(basedir + '/assets/fonts/helvetica.ttf', 36)
    conditionFont = ImageFont.truetype(basedir + '/assets/fonts/dejavu_sans_mono.ttf', 12)
    windFont = ImageFont.truetype(basedir + '/assets/fonts/dejavu_sans_mono.ttf', 12)
    textColor = 0
    
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
    weather = req('https://wttr.in/msp?format=j1', 'weather.json', 15)
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
    image.paste(Image.open(basedir + '/assets/weather_icons/' + icon + '.bmp'), (0, -2))
    
    drawText(draw, weatherDesc, conditionFont, textColor, 105, 22, 'left', 'center')
    drawText(draw, tempF + '°F', tempFont, textColor, 105, 50, 'left', 'center')
    drawText(draw, windKts + ' kts ' + windDir, windFont, textColor, 105, 78, 'left', 'center')
    
    status_bar_image = status_bar()
    image.paste(status_bar_image, (0, canvas_height - 22))
    
    return image
    
def status_bar():
    # Adjustable variables
    textSize = 12
    textFont = ImageFont.truetype(basedir + '/assets/fonts/dejavu_sans_mono.ttf', textSize)
    textColor = 0
    
    # Constants
    canvas_width = 250
    canvas_height = 22
    image = Image.new('1', (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(image)
    
    drawText(draw, time.strftime('%a, %b ') + str(int(time.strftime('%d'))), textFont, textColor, 6, 4, 'left', 'top')
    drawText(draw, time.strftime('%I:%M %p').lstrip('0'), textFont, textColor, canvas_width - 8, 4, 'right', 'top')
    draw.line([(0, 1), (canvas_width, 1)], fill=0, width=1)
    
    return image

# MARK: - Main
epd = None
stop_display_thread = False

def display_thread_function(update_queue):
    global stop_display_thread, epd
    
    try:
        if not simMode:
            epd = epd2in13_V4.EPD()
            epd.init()
            epd.Clear(0xFF)

            blank_image = Image.new('1', (250, 122), 255)
            blank_draw = ImageDraw.Draw(blank_image)
            epd.displayPartBaseImage(epd.getbuffer(blank_image))
            
        def update_screen():
            image = currentWeather()
            if simMode:
                update_queue.put(image)
            else:
                # image = image.rotate(180)
                epd.displayPartial(epd.getbuffer(image))

        update_screen()
        
        while not stop_display_thread:
            now = time.time()
            # Calculate the remaining time until the next full minute
            sleep_time = 60 - (now % 60)
            # Use shorter sleep intervals to check for stop requests more frequently
            for _ in range(int(sleep_time * 10)):  # Multiply by 10 to convert to 0.1 second intervals
                if stop_display_thread:
                    break
                time.sleep(0.1)
            if not stop_display_thread:
                update_screen()
                
    except IOError as e:
        logging.info(e)
    except Exception as e:
        logging.info(f"Display thread error: {e}")

# Start display thread
display_thread = threading.Thread(target=display_thread_function)
display_thread.daemon = True  # Thread will exit when main program exits
display_thread.start()


# Flask server
app = flask.Flask(__name__)

@app.route('/')
def index():
    return flask.send_file(basedir + '/index.html')

@app.route('/terminate')
def shutdown():
    logging.info("Terminating...")
    try:
        global stop_display_thread
        stop_display_thread = True
        # Allow time for display thread to stop
        time.sleep(1)
        
        # Schedule shutdown in a separate thread
        def shutdown_server():
            time.sleep(1)  # Give time for the response to be sent
            try:
                global epd
                if epd is not None:
                    logging.info("Clearing display...")
                    epd.init()
                    epd.Clear(0xFF)
                    epd.sleep()
                    epd2in13_V4.epdconfig.module_exit(cleanup=True)
                else:
                    logging.warning("EPD not initialized, skipping clear")
            except Exception as e:
                logging.error(f"Error clearing display: {str(e)}")
            finally:
                os._exit(0)  # Force exit the process
            
        threading.Thread(target=shutdown_server).start()
        return "Server shutting down..."
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")
        return f"Error during shutdown: {str(e)}", 500

if __name__ == "__main__":
    update_queue = queue.Queue()

    if simMode:
        def tk_update():
            try:
                while not update_queue.empty():
                    image = update_queue.get_nowait()
                    sim_image = ImageTk.PhotoImage(image)
                    sim_label.configure(image=sim_image)
                    sim_label.image = sim_image  # Keep a reference to avoid garbage collection
                sim_window.after(100, tk_update)
            except queue.Empty:
                pass

        sim_window = tk.Tk()
        sim_window.title("E-Paper Display Simulation")
        sim_label = tk.Label(sim_window)
        sim_label.pack()

        # Handle window close event
        def on_closing():
            global stop_display_thread
            stop_display_thread = True
            sim_window.destroy()

        sim_window.protocol("WM_DELETE_WINDOW", on_closing)
        sim_window.after(100, tk_update)

    # Start display thread
    display_thread = threading.Thread(target=display_thread_function, args=(update_queue,))
    display_thread.daemon = True  # Thread will exit when main program exits
    display_thread.start()

    # Flask server
    app = flask.Flask(__name__)

    @app.route('/')
    def index():
        return flask.send_file(basedir + '/index.html')

    @app.route('/terminate')
    def shutdown():
        logging.info("Terminating...")
        try:
            global stop_display_thread
            stop_display_thread = True
            # Allow time for display thread to stop
            time.sleep(1)
            
            # Schedule shutdown in a separate thread
            def shutdown_server():
                time.sleep(1)  # Give time for the response to be sent
                try:
                    global epd
                    if epd is not None:
                        logging.info("Clearing display...")
                        epd.init()
                        epd.Clear(0xFF)
                        epd.sleep()
                        epd2in13_V4.epdconfig.module_exit(cleanup=True)
                    else:
                        logging.warning("EPD not initialized, skipping clear")
                except Exception as e:
                    logging.error(f"Error clearing display: {str(e)}")
                finally:
                    os._exit(0)  # Force exit the process
                
            threading.Thread(target=shutdown_server).start()
            return "Server shutting down..."
        except Exception as e:
            logging.error(f"Error during shutdown: {str(e)}")
            return f"Error during shutdown: {str(e)}", 500

    if simMode:
        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5123)).start()
        sim_window.mainloop()
    else:
        app.run(host="0.0.0.0", port=5000)