import hashlib

SMS_USER = '21vianet_baremetal'
SMS_KEY = 'jDLw68K8QM6qu4GBEtniXylvPJIAPBks'
template_text = ""

param = {
    'smsUser': SMS_USER,
}

param = {
    'smsUser': SMS_USER,
    'templateName': "baremetal_code",
    'templateText': "您的账号正在更新绑定手机，旧手机验证码是：${code}。请在30分钟内完成验证。",
    'smsTypeStr': "0",
    'signName': "裸金属"
}

# 模板提审
param = {
    'smsUser': SMS_USER,
    'templateIdStr': "28041"
}

param = {
    'smsUser': SMS_USER,
    'templateIdStr': "28041",
    'templateName': "baremetal_verification_code",
    'templateText': "您的账号正在更好绑定手机，旧手机验证码是：${code}。",
    'smsTypeStr': "0",
    'signName': "裸金属"
}

param = {
    'smsUser': SMS_USER,
    'labelName': "世纪互联"
}

# 签名 添加
param = {
    'smsUser': SMS_USER,
    'signType': 0,
    'signName': "世纪互联"
}

param = {
    'smsUser': SMS_USER,
    'phone': "18101029680,13810207985,15010824266,18101023057",
    'signName': "世纪互联",
    'code': "1234",
    'labelId': 1925227,
}

param_keys = list(param.keys())
param_keys.sort()

param_str = ''
for key in param_keys:
    param_str += key + '=' + str(param[key]) + '&'

param_str = param_str[:-1]

sign_str = SMS_KEY + '&' + param_str + '&' + SMS_KEY
signature = hashlib.md5(sign_str.encode('utf8')).hexdigest()
print(signature)
