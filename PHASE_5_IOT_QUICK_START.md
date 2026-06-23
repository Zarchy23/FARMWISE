# PHASE_5_IOT_QUICK_START.md

# Phase 5: IoT Quick Start (15 Minutes)

## 🚀 30-Second Overview

Phase 5 lets you connect physical devices: soil sensors, weather stations, livestock trackers, cameras. Data flows automatically to Phase 4 dashboard.

**3 Ways to Send Data:**
1. **REST API** - WiFi devices HTTP POST
2. **MQTT** - Gateways, real-time streaming
3. **Webhooks** - Cloud IoT platforms

---

## ✅ Setup Checklist (5 minutes)

```bash
# 1. IoT app already added to settings.py
✓ core.iot in INSTALLED_APPS
✓ IoT URLs in core/urls.py

# 2. Create superuser (if not exists)
python manage.py createsuperuser

# 3. Run migrations
python manage.py makemigrations core.iot
python manage.py migrate

# 4. Access admin
# http://localhost:8000/admin
# Login and navigate to "IoT Device Management"
```

---

## 📱 Device Setup (5 minutes)

### Option A: REST API Device

**Step 1: Create Provisioning Token**
```bash
python manage.py shell
>>> from core.iot.models import DeviceProvisioningToken
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> Farm = __import__('core.models', fromlist=['Farm']).Farm
>>>
>>> token = DeviceProvisioningToken.objects.create(
...     token="dev-token-123456",
...     user=User.objects.first(),
...     farm=Farm.objects.first(),
...     device_type="weather_station",
...     device_name="Weather Station 1",
...     expires_at=timezone.now() + timedelta(hours=24)
... )
>>> print(f"Token: {token.token}")
Token: dev-token-123456
```

**Step 2: Register Device**
```bash
curl -X POST http://localhost:8000/api/iot/provisioning/register_device/ \
  -H "Content-Type: application/json" \
  -d '{
    "provisioning_token": "dev-token-123456",
    "device_name": "Weather Station 1",
    "device_type": "weather_station",
    "connection_type": "wifi"
  }'

# Response:
{
  "id": 1,
  "device_id": "DEV-FARM1-A1B2C3D4",
  "api_key": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Weather Station 1",
  "status": "active"
}
```

**Step 3: Add Sensors**
```bash
# List available sensor types
curl http://localhost:8000/api/iot/sensor-types/

# Add soil moisture sensor
curl -X POST http://localhost:8000/api/iot/devices/1/sensors/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "sensor_type": 1,
    "channel_name": "analog_0"
  }'
```

**Step 4: Submit Data**
```bash
curl -X POST http://localhost:8000/api/iot/data/submit/bulk/ \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "battery_level": 85,
    "data_points": [
      {"channel": "analog_0", "value": 45.3},
      {"channel": "analog_1", "value": 28.5}
    ]
  }'

# Response:
{
  "batch_id": 1,
  "total_submitted": 2,
  "successfully_processed": 2,
  "errors": []
}
```

### Option B: MQTT Device

**Step 1: Start Local Broker (Docker)**
```bash
docker run -it -p 1883:1883 eclipse-mosquitto
```

**Step 2: Publish Data**
```bash
mosquitto_pub -h localhost \
  -t "/farmwise/DEV-FARM1-A1B2C3D4/data" \
  -m '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "battery_level": 85,
    "data_points": [
      {"channel": "analog_0", "value": 45.3}
    ]
  }'
```

**Step 3: Start MQTT Consumer**
```bash
python manage.py mqtt_consumer --host localhost --port 1883
```

---

## 🔍 Verify Setup

### Check Device Created
```bash
curl -b "sessionid=XXX" http://localhost:8000/api/iot/devices/
```

### Check Latest Data
```bash
curl -b "sessionid=XXX" http://localhost:8000/api/iot/devices/1/latest_data/?limit=10
```

### Check Device Health
```bash
curl -b "sessionid=XXX" http://localhost:8000/api/iot/devices/1/health/
```

### Admin Dashboard
Navigate to: **http://localhost:8000/admin/core/iotdevice/**
- See all devices
- Check connection status
- View battery level
- See sensor count

---

## 🔌 Common Commands

### List Devices
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/iot/devices/
```

### Get Device Details
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/iot/devices/1/
```

### Send Command to Device
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/iot/devices/1/send_command/ \
  -d '{
    "command_type": "set_interval",
    "command_text": "SET_INTERVAL 600",
    "parameters": {"interval": 600}
  }'
```

### Update Device Location
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/iot/devices/1/update_location/ \
  -d '{
    "latitude": "-19.8563",
    "longitude": "29.1520",
    "location_description": "North Field"
  }'
```

### Get Sensor Data
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/iot/data/?device=1&limit=100
```

---

## 📊 Device Types Supported

| Type | Use Case | Connection |
|------|----------|-----------|
| soil_sensor | Soil moisture/NPK | WiFi/MQTT/LoRa |
| weather_station | Temperature/Humidity/Rain | WiFi/Cellular |
| camera | Pest detection/Photos | WiFi/Cellular |
| water_meter | Irrigation flow | WiFi/Pulse counter |
| temperature | Temperature only | WiFi/LoRa |
| humidity | Humidity only | WiFi/LoRa |
| ph_sensor | Soil pH | WiFi/LoRa |
| livestock_tracker | GPS + Vitals | Cellular/LoRa |
| pest_trap_monitor | Insect counts | WiFi/LoRa |
| sprinkler_controller | Smart irrigation | WiFi |
| livestock_scale | Weight tracking | WiFi/Bluetooth |
| egg_counter | Egg production | WiFi |
| custom | Your device | Any |

---

## 🐞 Quick Troubleshooting

**Device shows offline?**
```bash
# Check if device is still sending data
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/iot/devices/1/health/
# Look at: last_seen, consecutive_failures, last_error
```

**Data not appearing?**
```bash
# Check sensor is configured
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/iot/devices/1/sensors/

# Check device API key is correct
# Test with REST API first (easier to debug than MQTT)
```

**MQTT not connecting?**
```bash
# Verify broker is running
docker ps | grep mosquitto

# Check network connectivity
telnet localhost 1883

# Monitor messages
mosquitto_sub -h localhost -v -t "/farmwise/+/+"
```

**Admin interface not loading?**
```bash
# Run migrations
python manage.py migrate

# Restart Django
python manage.py runserver
```

---

## 📈 Next: Analytics Integration

Data from devices automatically appears in Phase 4 analytics:

```
Device → SensorDataPoint → DashboardMetric → Real-time Dashboard
                                          → Alerts
                                          → Performance Scores
                                          → Predictions
```

**View in Dashboard:**
1. Go to http://localhost:8000/dashboard
2. Look for real-time metrics
3. Check alerts tab
4. Performance shows device data

---

## 🎯 Common Use Cases (Copy-Paste)

### Soil Moisture Monitoring
```python
from core.iot.models import IoTDevice, SensorType, SensorConfiguration

device = IoTDevice.objects.get(id=1)

# Add soil moisture sensor
sensor_type = SensorType.objects.get(code='soil_moisture')
SensorConfiguration.objects.create(
    device=device,
    sensor_type=sensor_type,
    channel_name='analog_0',
    calibration_multiplier=0.95
)

# Set calibration thresholds
config = device.sensors.first()
config.warning_below = 30  # Dry
config.warning_above = 80  # Wet
config.save()
```

### Weather Station
```python
# Add multiple sensors
for sensor_code in ['air_temperature', 'air_humidity', 'rainfall']:
    sensor_type = SensorType.objects.get(code=sensor_code)
    SensorConfiguration.objects.create(
        device=device,
        sensor_type=sensor_type,
        channel_name=f'analog_{i}'
    )
```

### Livestock Tracking
```python
# Create GPS tracker device
device = IoTDevice.objects.create(
    device_id=f'DEV-GPS-{uuid4().hex[:8]}',
    name='Animal GPS Tracker',
    device_type='livestock_tracker',
    connection_type='cellular',
    user=farmer,
    farm=farm,
    power_source='battery'
)

# Add location sensors
for sensor_code in ['animal_location_lat', 'animal_location_lng']:
    SensorConfiguration.objects.create(
        device=device,
        sensor_type=SensorType.objects.get(code=sensor_code),
        channel_name=f'gps_{sensor_code[-3:]}'
    )
```

---

## 📚 Full Documentation

For complete API reference, device examples, and deployment:
👉 **[PHASE_5_IOT_DEVICE_INTEGRATION.md](PHASE_5_IOT_DEVICE_INTEGRATION.md)**

---

## ✨ What's Included

✅ IoT Device Models (11 models)
✅ REST API (25+ endpoints)
✅ MQTT Consumer (auto-ingest)
✅ Sensor Calibration
✅ Data Validation
✅ Device Health Tracking
✅ Admin Dashboard
✅ Analytics Integration
✅ Command System
✅ Provisioning Tokens

---

Status: ✅ Production Ready
Last Updated: 2025-01-15
