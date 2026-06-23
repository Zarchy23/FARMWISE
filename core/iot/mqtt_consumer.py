# core/iot/mqtt_consumer.py
# MQTT Consumer for IoT Device Data Ingestion
# Handles MQTT connection, message routing, and data processing

import paho.mqtt.client as mqtt
import json
import logging
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import threading
import queue

from core.models_iot import IoTDevice, SensorDataPoint, SensorConfiguration, DeviceHealth
from core.models_analytics import DashboardMetric

logger = logging.getLogger(__name__)


class MQTTConsumer:
    """
    MQTT consumer for IoT device data.
    
    Usage:
        consumer = MQTTConsumer(
            broker_host='localhost',
            broker_port=1883,
            username='farmwise',
            password='password'
        )
        consumer.connect()
        consumer.loop_start()  # Non-blocking
        # ... consumer will process messages in background
        consumer.disconnect()
    
    MQTT Topic Structure:
        /farmwise/{device_id}/data -> Sensor data submission
        /farmwise/{device_id}/status -> Device status updates
        /farmwise/{device_id}/commands/response -> Command responses
    """
    
    def __init__(self, broker_host='localhost', broker_port=1883, username=None, password=None):
        """Initialize MQTT consumer"""
        
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        
        # Create MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="farmwise-iot-consumer")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        
        # Set username/password if provided
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Enable TLS if using remote broker
        if broker_host != 'localhost' and broker_host != '127.0.0.1':
            try:
                self.client.tls_set()
                self.client.tls_insecure_set(False)
            except Exception as e:
                logger.warning(f"TLS setup failed: {e}")
        
        self.is_connected = False
        self.message_queue = queue.Queue()
        self.worker_thread = None
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            logger.info(f"MQTT connecting to {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.disconnect()
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def loop_start(self):
        """Start MQTT network loop (non-blocking)"""
        self.client.loop_start()
        logger.info("MQTT consumer loop started")
    
    def loop_stop(self):
        """Stop MQTT network loop"""
        self.client.loop_stop()
        logger.info("MQTT consumer loop stopped")
    
    def loop_forever(self):
        """Start MQTT network loop (blocking)"""
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("MQTT consumer interrupted")
        finally:
            self.client.disconnect()
    
    # ============================================================
    # MQTT CALLBACKS
    # ============================================================
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Called when client connects to broker"""
        if rc == 0:
            logger.info("MQTT connected successfully")
            self.is_connected = True
            # Subscribe to data topics
            client.subscribe("/farmwise/+/data", qos=1)
            client.subscribe("/farmwise/+/status", qos=1)
            client.subscribe("/farmwise/+/commands/response", qos=1)
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """Called when message received"""
        try:
            # Route message based on topic
            parts = msg.topic.split('/')
            
            if len(parts) >= 4:
                device_id = parts[2]
                message_type = parts[3]
                
                if message_type == 'data':
                    self.message_queue.put({
                        'type': 'data',
                        'device_id': device_id,
                        'payload': msg.payload.decode('utf-8')
                    })
                    self._process_sensor_data(device_id, msg.payload.decode('utf-8'))
                
                elif message_type == 'status':
                    self.message_queue.put({
                        'type': 'status',
                        'device_id': device_id,
                        'payload': msg.payload.decode('utf-8')
                    })
                    self._process_device_status(device_id, msg.payload.decode('utf-8'))
                
                elif message_type == 'commands' and len(parts) >= 5 and parts[4] == 'response':
                    self.message_queue.put({
                        'type': 'command_response',
                        'device_id': device_id,
                        'payload': msg.payload.decode('utf-8')
                    })
                    self._process_command_response(device_id, msg.payload.decode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when client disconnects"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"MQTT unexpected disconnection: {rc}")
        else:
            logger.info("MQTT disconnected cleanly")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """Called when subscription confirmed"""
        logger.info(f"MQTT subscription confirmed with QoS {granted_qos}")
    
    # ============================================================
    # MESSAGE PROCESSING
    # ============================================================
    
    def _process_sensor_data(self, device_id, payload_str):
        """Process sensor data message"""
        try:
            payload = json.loads(payload_str)
            
            # Find device
            device = IoTDevice.objects.get(device_id=device_id)
            
            with transaction.atomic():
                timestamp = timezone.now()
                data_points = payload.get('data', [])
                
                for point in data_points:
                    channel = point.get('channel')
                    value = point.get('value')
                    
                    try:
                        # Find sensor configuration
                        sensor_config = SensorConfiguration.objects.get(
                            device=device,
                            channel_name=channel,
                            is_active=True
                        )
                        
                        # Calibrate value
                        calibrated_value = sensor_config.calibrate_reading(value)
                        
                        # Create data point
                        data_point = SensorDataPoint.objects.create(
                            device=device,
                            sensor_config=sensor_config,
                            raw_value=str(value),
                            value=calibrated_value,
                            device_timestamp=timestamp,
                            signal_strength=point.get('signal_strength'),
                            is_valid=True
                        )
                        
                        # Map to analytics metric
                        self._map_to_analytics(device, sensor_config, calibrated_value, timestamp)
                        
                        logger.debug(f"Processed sensor data: {device_id}/{channel} = {calibrated_value}")
                    
                    except SensorConfiguration.DoesNotExist:
                        logger.warning(f"Sensor not configured: {device_id}/{channel}")
                
                # Update device metadata
                device.last_data_received = timezone.now()
                device.last_seen = timezone.now()
                if 'battery_level' in payload:
                    device.battery_level = payload['battery_level']
                device.offline_alert_sent = False
                device.save()
                
                # Update health
                health = DeviceHealth.objects.get(device=device)
                health.total_readings += len(data_points)
                health.successful_readings += len(data_points)
                health.consecutive_failures = 0
                health.save()
                
                logger.info(f"Processed {len(data_points)} sensor readings from {device_id}")
        
        except IoTDevice.DoesNotExist:
            logger.warning(f"Device not found: {device_id}")
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
    
    def _process_device_status(self, device_id, payload_str):
        """Process device status update"""
        try:
            payload = json.loads(payload_str)
            
            device = IoTDevice.objects.get(device_id=device_id)
            
            # Update device fields
            device.battery_level = payload.get('battery_level', device.battery_level)
            device.status = payload.get('status', device.status)
            device.last_seen = timezone.now()
            device.save()
            
            # Update health if error reported
            if payload.get('error'):
                health = DeviceHealth.objects.get(device=device)
                health.last_error = payload.get('error')
                health.last_error_time = timezone.now()
                health.consecutive_failures += 1
                health.save()
                logger.warning(f"Device error reported: {device_id} - {payload.get('error')}")
            
            logger.info(f"Updated device status: {device_id}")
        
        except IoTDevice.DoesNotExist:
            logger.warning(f"Device not found: {device_id}")
        except Exception as e:
            logger.error(f"Error processing device status: {e}")
    
    def _process_command_response(self, device_id, payload_str):
        """Process command response from device"""
        try:
            from core.models_iot import DeviceCommand
            
            payload = json.loads(payload_str)
            command_id = payload.get('command_id')
            
            if not command_id:
                return
            
            command = DeviceCommand.objects.get(id=command_id, device__device_id=device_id)
            
            # Update command status
            command.status = payload.get('status', 'executed')
            command.executed_at = timezone.now()
            command.result = payload.get('result', '')
            command.save()
            
            logger.info(f"Command response received: {command_id} - {command.status}")
        
        except DeviceCommand.DoesNotExist:
            logger.warning(f"Command not found: {device_id}/{command_id}")
        except Exception as e:
            logger.error(f"Error processing command response: {e}")
    
    def _map_to_analytics(self, device, sensor_config, value, timestamp):
        """Map sensor data to analytics dashboard metric"""
        
        sensor_to_metric_map = {
            'soil_moisture': 'soil_moisture',
            'air_temperature': 'temperature',
            'air_humidity': 'humidity',
            'rainfall': 'rainfall',
            'soil_temperature': 'soil_temperature',
            'soil_ph': 'ph',
            'nitrogen': 'nitrogen',
            'crop_height': 'crop_health',
            'water_flow': 'water_usage',
            'pest_count': 'pest_count',
        }
        
        metric_type = sensor_to_metric_map.get(sensor_config.sensor_type.code)
        if not metric_type:
            return
        
        try:
            metric, created = DashboardMetric.objects.get_or_create(
                farm=device.farm,
                metric_type=metric_type,
                defaults={'value': float(value), 'source': 'iot_mqtt'}
            )
            
            if not created:
                metric.value = float(value)
                metric.save()
        except Exception as e:
            logger.error(f"Error mapping to analytics: {e}")


def start_mqtt_consumer(broker_host='localhost', broker_port=1883, username=None, password=None):
    """Helper function to start MQTT consumer"""
    consumer = MQTTConsumer(broker_host, broker_port, username, password)
    
    if consumer.connect():
        consumer.loop_start()
        return consumer
    else:
        logger.error("Failed to start MQTT consumer")
        return None


def stop_mqtt_consumer(consumer):
    """Helper function to stop MQTT consumer"""
    if consumer:
        consumer.loop_stop()
        consumer.disconnect()
