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

logging.basicConfig(level=logging.DEBUG)


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
            image = timeMeridiem()
            if simMode:
                update_queue.put(image)
            else:
                image = image.rotate(180)
                epd.displayPartial(epd.getbuffer(image))

        update_screen()
        
        while not stop_display_thread:
            now = time.time()
            # Calculate the remaining time until the next full minute
            sleep_time = 60 - (now % 60) + 1
            # Use shorter sleep intervals to check for stop requests more frequently
            for _ in range(int(sleep_time)):
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