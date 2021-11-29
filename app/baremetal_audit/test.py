# -*- coding: utf-8 -*-
import json
from oslo_config import cfg
import oslo_messaging as messaging

CONF = cfg.CONF
# messaging.set_transport_defaults('websocket')
messaging.set_transport_defaults('cloudaudit')
# CONF.set_override("security_protocol", 'SASL_PLAINTEXT', 'oslo_messaging_kafka')

# transport = messaging.get_transport(cfg.CONF,url="rabbit://admin:admin@10.200.2.187:5672/",)
# transport = messaging.get_transport(cfg.CONF,url="rabbit://vianet_guest:vianet_guest@10.200.2.187:5672/vianet_guest",)
transport = messaging.get_notification_transport(CONF, url="kafka://@10.200.2.200:9092/", )

notifier = messaging.Notifier(transport,
                                      driver='messagingv2', topics=['log_audit'])
notifier2 = notifier.prepare(publisher_id='compute222')
payload = {'platform': 'BAREMETAL', 'region': 'regionOne', 'project_id': None, 'user_id': None, 'service_type': None,
                   'resource_type': None, 'resource_id': None, 'resource_name': None, 'contrace_number': None,
                              'time': '1589353917.01999', 'trace_name': None, 'trace_type': None, 'source_ip': None, 'request': None,
                                         'response': None, 'code': 200}
notifier2.info(ctxt={}, event_type='cloud_audit.log', payload=payload)


from confluent_kafka import Producer


conf = {
         'bootstrap.servers': '10.200.2.200:9092',
         'client.id': '23a49894'
     }

p = Producer(conf)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))



    # Asynchronously produce a message, the delivery report callback
    # will be triggered from poll() above, or flush() below, when the message has
    # been successfully delivered or failed permanently.
# payload = json.dumps(payload).encode('utf-8')
# p.poll(0)
# p.produce('log_audit.info', payload)
# p.poll(0.1)
# Wait for any outstanding messages to be delivered and delivery report
# callbacks to be triggered.
# p.flush()

