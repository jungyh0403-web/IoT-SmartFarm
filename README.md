# 🌱 IoT SmartFarm
**Raspberry Pi 기반 IoT 스마트팜 자동화 시스템**

센서 데이터 수집부터 조건 기반 자동 제어,  
웹 대시보드를 통한 실시간 모니터링까지 하나의 시스템으로 구현한 IoT SmartFarm 프로젝트.

---

## 📌 프로젝트 개요
IoT SmartFarm은 농작물 재배 환경(온도, 습도, 토양 수분, 조도, 수위 등)을  
실시간으로 모니터링하고, 설정된 조건에 따라 관수·환기·조명·개폐를 자동으로 제어하는  
Raspberry Pi 기반 스마트 농장 자동화 시스템.

- **개발 기간**: 2024.09 ~ 2024.12
- **개발 인원**: 3명
- **수상 이력**
  - 학과 경진대회 **최우수상**
  - 교내 경진대회 **장려상**

---

## 👨‍💻 담당 역할
본 프로젝트에서 하드웨어 제어와 소프트웨어 연동을 중심으로 담당함.

- Python 기반 센서 데이터 수집 및 제어 로직 구현
- MCP3008 ADC(SPI) 기반 아날로그 센서 인터페이스 구현
- Flask 웹 서버 및 REST API 설계
- JavaScript 기반 웹 대시보드(UI, 그래프) 구현
- 자동/수동 제어 로직 설계
- 회로 구성 및 배선 일부 담당
- MCP3008 ADC 통신 오류 분석 및 문제 해결

---

## 🛠 기술 스택

### Hardware
- Raspberry Pi 4
- DHT11 (온습도 센서)
- MCP3008 (ADC)
- 토양 수분 센서
- 조도 센서
- 수위 센서
- DC Motor / Servo Motor
- Relay Module
- I2C LCD

### Software
- Python
- Flask
- HTML / CSS / JavaScript
- AJAX
- Chart.js
- GPIO / SPI / I2C

---

## 🧩 시스템 구조
센서 데이터를 Raspberry Pi에서 수집하고,  
Flask 웹 서버를 통해 데이터를 제공하며  
웹 대시보드에서 실시간 모니터링 및 제어가 가능하도록 구성.

