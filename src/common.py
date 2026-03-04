import time
import base64
import requests
import re
import json
import urllib.parse
from getpass import getpass

def printline():
    print('---------------------------------------------------')

def generate_cipher_text(password):
    """
    WeLearn 登录密码前端加密算法的 Python 还原
    该算法通过当前时间戳与密码的各个字节进行异或等位运算生成校验位，并做 Base64 包装
    """
    t0 = int(time.time() * 1000)
    p_bytes = password.encode('utf-8')
    v = (t0 >> 16) & 255
    for b in p_bytes:
        v ^= b
    remainder = v % 100
    t1 = (t0 // 100) * 100 + remainder
    p1 = "".join([format(b, '02x') for b in p_bytes])
    s = f"{t1}*{p1}"
    encrypted = base64.b64encode(s.encode('utf-8')).decode('utf-8')
    return encrypted, t1

def login_by_password(username, password) -> requests.Session:
    """账号密码方式登录 WeLearn 并返回 Session"""
    session = requests.Session()
    encrypted_pwd, timestamp = generate_cipher_text(password)
    
    login_data = {
        'rturl': '/connect/authorize/callback?client_id=welearn_web&redirect_uri=https%3A%2F%2Fwelearn.sflep.com%2Fsignin-sflep&response_type=code&scope=openid%20profile%20email%20phone%20address&code_challenge=p18_2UckWpdGfknVKQp6Ang64zAYH6__0Z8eQu2uuZE&code_challenge_method=S256&state=OpenIdConnect.AuthenticationProperties%3DBhc1Qn6lYFZrxO_KhC7UzXZTYACtsAnIVT0PgzDlhtuxIXeSFLwXaNbthEeuwSCbzvhrw2wECCxFTq8tbd7k2OFPfH0_TCnMkuh8oBFmlhEsZ3ZXUYecidfT2h2YpAyAoaBaXfpuQj2SGCIEW3KVRYpnljmx-mso97xCbjz72URywiBJRMqDS9TqY-0vaviUIH1X72u_phfuiBdbR1s-WOyUj21KAPdNPJXi1nQtUd-hRoeI53WBTrv2EC0U4SNFvhivPgE6YseB2fdYbPv4u0NiFeHPD3EBQyqE_iUVI1QrGPG3VvhD5xs8odx21WncybewKIuTQpH3MAfJkTmDeQ&x-client-SKU=ID_NET472&x-client-ver=6.32.1.0',
        'account': username,
        'pwd': encrypted_pwd,
        'ts': str(timestamp)
    }
    
    login_headers = {
        'host': 'sso.sflep.com',
        'sec-ch-ua-platform': '"Windows"',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://sso.sflep.com',
        'referer': 'https://sso.sflep.com/idsvr/login.html'
    }

    try:
        res = session.post('https://sso.sflep.com/idsvr/account/login', data=login_data, headers=login_headers)
        if res.ok and 'code' in res.json() and res.json()['code'] == 0:
            print('登录成功!!')
            
            # 手动执行 OAuth 回调来获取 welearn.sflep.com 的正式 cookie
            callback_url = 'https://sso.sflep.com/idsvr/connect/authorize/callback'
            callback_params = {
                'client_id': 'welearn_web',
                'redirect_uri': 'https://welearn.sflep.com/signin-sflep',
                'response_type': 'code',
                'scope': 'openid profile email phone address',
                'code_challenge': 'p18_2UckWpdGfknVKQp6Ang64zAYH6__0Z8eQu2uuZE',
                'code_challenge_method': 'S256',
                'state': 'OpenIdConnect.AuthenticationProperties=Bhc1Qn6lYFZrxO_KhC7UzXZTYACtsAnIVT0PgzDlhtuxIXeSFLwXaNbthEeuwSCbzvhrw2wECCxFTq8tbd7k2OFPfH0_TCnMkuh8oBFmlhEsZ3ZXUYecidfT2h2YpAyAoaBaXfpuQj2SGCIEW3KVRYpnljmx-mso97xCbjz72URywiBJRMqDS9TqY-0vaviUIH1X72u_phfuiBdbR1s-WOyUj21KAPdNPJXi1nQtUd-hRoeI53WBTrv2EC0U4SNFvhivPgE6YseB2fdYbPv4u0NiFeHPD3EBQyqE_iUVI1QrGPG3VvhD5xs8odx21WncybewKIuTQpH3MAfJkTmDeQ'
            }
            session.get(callback_url, params=callback_params, allow_redirects=True)
            
            # 由于依赖外部库可能丢失，转换为纯净的 Cookie 字符串方便通用
            cookies_list = []
            for cookie in session.cookies:
                cookies_list.append(cookie.name + "=" + cookie.value)
            session.cookies_str = '; '.join(cookies_list)
            return session
        else:
            print('登录失败:', res.text)
            return None
    except Exception as e:
        print('登录请求发生错误:', e)
        return None

def login_by_cookie(cookie_str) -> requests.Session:
    """Cookie 登录方式，直接附加用户提供的 cookie 数据"""
    session = requests.Session()
    # 模拟检查 cookie 是否有效
    session.cookies_str = cookie_str
    if 'clist' in cookie_str:
        print('登录成功!!!')
        return session
    else:
        print('Cookie输入格式可能有误(应包含 clist)，继续尝试...')
        return session

def get_course_list(session):
    """获取所有课程信息"""
    url = 'https://welearn.sflep.com/ajax/authCourse.aspx'
    headers = {
        'host': 'welearn.sflep.com',
        'sec-ch-ua-platform': '"Windows"',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://welearn.sflep.com/student/index.aspx',
        'Cookie': session.cookies_str
    }
    params = {'action': 'gmc'}
    try:
        response = session.get(url, params=params, headers=headers)
        try:
            json_data = response.json()
            return json_data
        except ValueError:
            if '<script' in response.text:
                print('登录状态已失效，需要重新登录')
            return None
    except Exception as e:
        print('请求发生错误:', str(e))
        return None

def init_login():
    """统一切口：供其他脚本交互使用"""
    print('==================请选择登录方式==================')
    loginmode = input('请选择登录方式: \n  1.账号密码登录 \n  2.Cookie登录\n\n请输入数字1或2: ')
    printline()
    
    session = None
    if loginmode == '1':
        username = input('请输入账号: ')
        password = getpass('请输入密码: ')
        session = login_by_password(username, password)
    elif loginmode == '2':
        cookie_str = input('请粘贴Cookie: ').strip()
        session = login_by_cookie(cookie_str)
    else:
        print('输入错误!!')
        
    if not session:
        print('发生错误!!!可能是登录错误或没有网络!!!')
        input('按任意键退出')
        exit(0)
    return session
