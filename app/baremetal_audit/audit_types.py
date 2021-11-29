# -*- coding: utf-8 -*-


GLOBAL = 'global'
NATIONAL = 'national'

# service_types
FIREWALL = 'FIREWALL'
VPC = 'VPC'
ECBM = 'ECBM'
EIP = "EIP"
SBW = "SHAREBANDWIDTH"
NATWAGEWAY = 'NATGATEWAY'
NATRULE = 'NATRULE'

IAM = 'IAM'


# resource_types

NETWORK = 'NETWORK'
KEYPAIR = 'KEYPAIR'
USER = 'USER'



FIREWALL_RULE = 'FIREWALL_RULE'

# trace_name
CREATE = 'create'
UPDATE = 'update'
DELETE = 'delete'
REBOOT = 'reboot'  # 重启
STOP = 'stop'      # 停止
START = 'start'    # 启动
INTERFACT_ATTACH = 'interface_attach'   # 连接网络
INTERFACE_DETACH = 'interface_detach'   # 分离网络
EIP_ATTACH = 'elasitc_ip_attach'
EIP_DETACH = 'elasitc_ip_detach'
VNC = 'vnc'   # 远程登录

LOGIN = 'login'
LOGOUT ='logout'


EIP_AS_FIREWALL = 'elasitc_ip_associate_firewall'
EIP_UPDATE_BANDWIDTH = 'elasitc_ip_update_bandwidth'


#
SBW_ADD_EIP = 'share_bandwidth_add_eip'   # 添加ip
SBW_REMOVE_EIP = 'share_bandwidth_remove_eip' # 移除ip


# trace_type
CONSOLEACTION = 'ConsoleAction'
SYSTEMACTION = 'SystemAction'
APICALL = 'ApiCall'




