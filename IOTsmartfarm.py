import RPi.GPIO as GPIO
import dht11
from time import sleep
from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS
import spidev
import threading
from RPLCD.i2c import CharLCD  # I2C LCD 모듈 추가

app = Flask(__name__)
CORS(app)  # 모든 도메인에서의 접근 허용

# GPIO 핀 설정
MOTOR_A_IN1 = 17
MOTOR_A_IN2 = 18
MOTOR_B_IN1 = 22
MOTOR_B_IN2 = 23
ENA = 24          # 모터 A 속도 제어 핀 (PWM)
ENB = 25          # 모터 B 속도 제어 핀 (PWM)
SERVO_PIN = 20    # 서보 모터 핀
DHT_PIN = 4       # DHT11 센서 핀
RELAY_PIN = 16    # 릴레이 신호 핀

# MCP3008 설정
SPI_BUS = 0
SPI_DEVICE = 0

# I2C LCD 설정
LCD_I2C_ADDRESS = 0x27  # I2C 주소
lcd = CharLCD('PCF8574', LCD_I2C_ADDRESS)  # CharLCD 객체 생성

# 초기 GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_A_IN1, GPIO.OUT)
GPIO.setup(MOTOR_A_IN2, GPIO.OUT)
GPIO.setup(MOTOR_B_IN1, GPIO.OUT)
GPIO.setup(MOTOR_B_IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)  # ENA 핀을 출력으로 설정
GPIO.setup(ENB, GPIO.OUT)  # ENB 핀을 출력으로 설정
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(DHT_PIN, GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)  # 릴레이 핀 설정

# PWM 설정
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

# MCP3008 SPI 초기화
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1350000

# DHT11 초기화
instance = dht11.DHT11(pin=DHT_PIN)

# 전역 변수
auto_thresholds = {
    'soil': 0,
    'water': [300, 600, 900],
    'temp': 25,
    'humidity': 50
}

mode = '자동'  # '자동' 또는 '수동'

# 센서 데이터 전역 변수
sensor_data = {
    'temperature': 0,
    'humidity': 0
}

lock = threading.Lock()
previous_temperature = None  # 이전 온도를 저장할 변수

def read_channel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


def control_automatic():
    global previous_temperature
    while True:
        if mode == '자동':  # 모드가 자동일 때만 실행
            with lock:
                # MCP3008 센서 읽기
                soil_moisture = read_channel(7)  # 토양 수분
                water_level = read_channel(6)     # 수위
                light_level = read_channel(0)      # 조도 센서 (CH2)

                # 조도 센서 값에 따라 LED 제어
                if light_level > 600:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)  # LED 켜기
                else:
                    GPIO.output(RELAY_PIN, GPIO.LOW)   # LED 끄기

                # 모터 제어 로직 (펌프)
                if soil_moisture < auto_thresholds['soil']:
                    GPIO.output(MOTOR_A_IN1, GPIO.HIGH)
                    GPIO.output(MOTOR_A_IN2, GPIO.LOW)
                    GPIO.output(ENA, GPIO.HIGH)  # ENA 핀 활성화
                else:
                    GPIO.output(MOTOR_A_IN1, GPIO.LOW)
                    GPIO.output(MOTOR_A_IN2, GPIO.LOW)
                    GPIO.output(ENA, GPIO.LOW)  # ENA 핀 비활성화

                # 온습도 관리 및 팬 제어
                if sensor_data['temperature'] > auto_thresholds['temp'] or sensor_data['humidity'] > auto_thresholds['humidity']:
                    GPIO.output(MOTOR_B_IN1, GPIO.HIGH)
                    GPIO.output(MOTOR_B_IN2, GPIO.LOW)
                    GPIO.output(ENB, GPIO.HIGH)  # ENB 핀 활성화
                else:
                    GPIO.output(MOTOR_B_IN1, GPIO.LOW)
                    GPIO.output(MOTOR_B_IN2, GPIO.LOW)
                    GPIO.output(ENB, GPIO.LOW)  # ENB 핀 비활성화

                # 서보 모터 제어
                if sensor_data['temperature'] > auto_thresholds['temp']:
                    GPIO.setup(SERVO_PIN, GPIO.OUT)
                    servo.ChangeDutyCycle(12)  # 예시로 180도
                    sleep(0.3)
                    GPIO.setup(SERVO_PIN, GPIO.IN)
                elif sensor_data['temperature'] < auto_thresholds['temp']:
                    GPIO.setup(SERVO_PIN, GPIO.OUT)
                    servo.ChangeDutyCycle(2)  # 예시로 0도
                    sleep(0.3)
                    GPIO.setup(SERVO_PIN, GPIO.IN)

        sleep(1)

def update_lcd():
    while True:
        result = instance.read()
        if result.is_valid():
            with lock:
                sensor_data['temperature'] = int(result.temperature)
                sensor_data['humidity'] = int(result.humidity)
            
            # LCD에 온도와 습도 값 표시
            lcd.clear()  # LCD 초기화
            lcd.write_string(f' IoT SMART FARM')
            lcd.cursor_pos = (1, 0)  # 두 번째 줄로 이동
            lcd.write_string(f' T: {sensor_data["temperature"]}C  H: {sensor_data["humidity"]}%')
        
        sleep(2)  # 2초마다 업데이트

@app.route('/auto', methods=['GET', 'POST'])
def auto_mode():
    global auto_thresholds, mode
    mode = '자동'  # 자동 모드로 설정

    if request.method == 'POST':
        try:
            auto_thresholds['soil'] = int(request.form.get('threshold_soil', auto_thresholds['soil']))
            auto_thresholds['water'] = [
                int(request.form.get('threshold_water1', auto_thresholds['water'][0])),
                int(request.form.get('threshold_water2', auto_thresholds['water'][1])),
                int(request.form.get('threshold_water3', auto_thresholds['water'][2]))
            ]
            auto_thresholds['temp'] = int(request.form.get('threshold_temp', auto_thresholds['temp']))
            auto_thresholds['humidity'] = int(request.form.get('threshold_humidity', auto_thresholds['humidity']))
            return redirect(url_for('auto_mode'))
        except Exception as e:
            print(f"Error updating thresholds: {e}")
            return "Invalid input", 400  # 잘못된 입력에 대한 응답

    with lock:
        light_level = read_channel(2)  # 조도 센서 값
        return render_template('auto.html', thresholds=auto_thresholds, sensor_data=sensor_data, light_level=light_level)

@app.route('/sensor_data', methods=['GET'])
def sensor_data_endpoint():
    with lock:
        return {
            'temperature': sensor_data['temperature'],
            'humidity': sensor_data['humidity'],
            'soil_moisture': read_channel(7),  # 토양 수분
            'water_level': read_channel(6),     # 수위
            'light_level': read_channel(0),      # 조도 센서 값 추가
        }

@app.route('/')
def sensor_graph():
    return render_template('sensor_graph.html')  # 새로운 그래프 페이지 렌더링

@app.route('/manual', methods=['GET', 'POST'])
def manual_mode():
    global mode
    mode = '수동'  # 수동 모드로 설정
    try:
        if request.method == 'POST':
            with lock:
                if 'pump' in request.form:
                    action = request.form['pump']
                    if action == 'on':
                        GPIO.output(MOTOR_A_IN1, GPIO.HIGH)
                        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
                        GPIO.output(ENA, GPIO.HIGH)  # ENA 핀 활성화
                    else:
                        GPIO.output(MOTOR_A_IN1, GPIO.LOW)
                        GPIO.output(MOTOR_A_IN2, GPIO.LOW)
                        GPIO.output(ENA, GPIO.LOW)  # ENA 핀 비활성화

                if 'fan' in request.form:
                    action = request.form['fan']
                    if action == 'on':
                        GPIO.output(MOTOR_B_IN1, GPIO.HIGH)
                        GPIO.output(MOTOR_B_IN2, GPIO.LOW)
                        GPIO.output(ENB, GPIO.HIGH)  # ENB 핀 활성화
                    else:
                        GPIO.output(MOTOR_B_IN1, GPIO.LOW)
                        GPIO.output(MOTOR_B_IN2, GPIO.LOW)
                        GPIO.output(ENB, GPIO.LOW)  # ENB 핀 비활성화

                if 'window' in request.form:
                    window_action = request.form['window']  # 서보모터 제어 로직
                    if window_action == 'open':  # 서보모터를 180도로 이동
                        GPIO.setup(SERVO_PIN, GPIO.OUT)
                        servo.ChangeDutyCycle(12)  # 예시로 180도
                        sleep(0.3)
                        GPIO.setup(SERVO_PIN, GPIO.IN)
                    elif window_action == 'close':  # 서보모터를 0도로 이동
                        GPIO.setup(SERVO_PIN, GPIO.OUT)
                        servo.ChangeDutyCycle(2)  # 예시로 0도
                        sleep(0.3)
                        GPIO.setup(SERVO_PIN, GPIO.IN)

                # LED 제어 추가
                if 'led' in request.form:
                    led_action = request.form['led']
                    if led_action == 'on':
                        GPIO.output(RELAY_PIN, GPIO.HIGH)  # LED 켜기
                    else:
                        GPIO.output(RELAY_PIN, GPIO.LOW)   # LED 끄기

            return redirect(url_for('manual_mode'))

        # GET 요청일 경우 센서 데이터 업데이트
        with lock:
            temperature = sensor_data['temperature']
            humidity = sensor_data['humidity']
            soil_moisture = read_channel(7)  # 토양 수분
            water_level = read_channel(6)     # 수위
            light_level = read_channel(0)      # 조도 센서 값 읽기

        return render_template('manual.html', sensor_data={
            'temperature': temperature,
            'humidity': humidity,
            'soil_moisture': soil_moisture,
            'water_level': water_level,
            'light_level': light_level  # 조도 센서 값 추가
        })

    except Exception as e:
        print("Error:", e)  # 콘솔에 에러 출력
        return "Internal Server Error", 500

if __name__ == '__main__':
    try:
        # 자동 제어 쓰레드 시작
        print("자동 제어 스레드 시작")
        threading.Thread(target=control_automatic, daemon=True).start()

        # DHT11 센서와 LCD 업데이트를 위한 스레드 시작
        threading.Thread(target=update_lcd, daemon=True).start()
        
        # Flask 서버 시작
        app.run(host='호스트 서버 IP', port=8080)
    finally:
        servo.stop()
        GPIO.cleanup()

