import network
import socket
from machine import Pin
from dht import DHT11
import utime as time

# WiFi credentials
SSID = 'BOLT_CAM'
PASSWORD = 'Madras@009'

# DHT11 sensor setup
pin = Pin(16, Pin.OUT, Pin.PULL_DOWN)
sensor = DHT11(pin)

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# Wait for connection
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Check if connected
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    ip_address = status[0]
    print('IP = ' + ip_address)

# Simple web server
def web_page(temp, hum, ip):
    html = """
    <html>
        <head>
            <title>Temperature and Humidity</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="5">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f9;
                }}
                h1 {{
                    color: #333;
                    font-size: 2em;
                }}
                p {{
                    font-size: 1.2em;
                    color: #666;
                }}
                .container {{
                    padding: 20px;
                    margin-top: 50px;
                }}
                .meter {{
                    margin: 20px;
                    width: 80%;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 0.8em;
                    color: #aaa;
                }}
                @media (max-width: 600px) {{
                    h1 {{
                        font-size: 1.5em;
                    }}
                    p {{
                        font-size: 1em;
                    }}
                    .meter {{
                        width: 100%;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Temperature and Humidity Monitor</h1>
                <p>Temperature: {} &#8451;</p>
                <meter class="meter" value="{}" min="0" max="50"></meter>
                <p>Humidity: {} %</p>
                <meter class="meter" value="{}" min="0" max="100"></meter>
                <div class="footer">
                    <p>IP Address: {}</p>
                </div>
            </div>
        </body>
    </html>
    """.format(temp, temp, hum, hum, ip)
    return html

# Setup socket web server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(5)

print('listening on', addr)

while True:
    try:
        sensor.measure()
        temp = sensor.temperature
        hum = sensor.humidity
        print("Measured Temperature: {} °C, Humidity: {} %".format(temp, hum))
    except Exception as e:
        print("Measurement failed: {}".format(e))
        temp = 'N/A'
        hum = 'N/A'

    cl, addr = s.accept()
    print('client connected from', addr)
    cl_file = cl.makefile('rwb', 0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break

    response = web_page(temp, hum, ip_address)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(response)
    cl.close()

