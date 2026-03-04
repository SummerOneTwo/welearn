import re
import urllib.parse
from common import init_login, get_course_list, printline

def get_course_info(session, cid):
    """提取课程内容页面信息以获取 classid, uid 和 scoid 列表"""
    url = f'https://welearn.sflep.com/student/course_info.aspx?cid={cid}'
    headers = {
        'host': 'welearn.sflep.com',
        'referer': 'https://welearn.sflep.com/student/index.aspx',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Cookie': session.cookies_str
    }
    
    res = session.get(url, headers=headers)
    
    # 利用正则简单匹配 uid 和 classid
    uid_search = re.search(r'"uid":(.*?),', res.text)
    class_search = re.search(r'"classid":"(.*?)"', res.text)
    
    if not uid_search or not class_search:
        print('获取基本信息失败!!')
        return None, None, None
        
    uid = uid_search.group(1)
    classid = class_search.group(1)

    # 提交 AJAX 请求获取具体单元列表
    ajaxUrl = 'https://welearn.sflep.com/ajax/StudyStat.aspx'
    data = {'action': 'courseunits', 'cid': cid, 'uid': uid}
    infoHeaders = headers.copy()
    infoHeaders['Referer'] = 'https://welearn.sflep.com/student/course_info.aspx'
    
    units_res = session.post(ajaxUrl, data=data, headers=infoHeaders)
    try:
        units_json = units_res.json()
        return uid, classid, units_json.get('info', [])
    except Exception as e:
        print('处理课程数据时发生错误:', e)
        return None, None, None

def start_curr_spammer(session, cid, uid, classid, unit, crate):
    """单元过检测：依次发包 startsco160928, setscoinfo, savescoinfo160928"""
    unitidx = unit.get('unitidx')
    ajaxUrl = f'https://welearn.sflep.com/ajax/StudyStat.aspx?action=scoLeaves&cid={cid}&uid={uid}&unitidx={unitidx}&classid={classid}'
    
    headers = {
        'host': 'welearn.sflep.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Cookie': session.cookies_str,
        'Referer': f'https://welearn.sflep.com/Student/StudyCourse.aspx?cid={cid}'
    }
    
    leaves_res = session.get(ajaxUrl, headers=headers)
    try:
        sco_list = leaves_res.json().get('info', [])
    except Exception as e:
        print('    出错了', e)
        return False

    success = 0
    fail = 0

    scoUrl = 'https://welearn.sflep.com/Ajax/SCO.aspx'
    
    for sco in sco_list:
        if sco.get('isvisible') == 'false':
            print('    [!!跳过!!]    ', sco.get('location', '未知'))
            continue

        if sco.get('iscomplete') == 'True':
            print('    [ 已完成 ]    ', sco.get('location', '未知'))
            continue
            
        print('    [即将完成]    ', sco.get('location', '未知'))
        scoid = sco.get('id')
        
        # 1. 触发 startsco160928 开启记录
        data_start = {'action': 'startsco160928', 'cid': cid, 'scoid': scoid, 'uid': uid}
        session.post(scoUrl, data=data_start, headers=headers)
        
        # 2. 注入满分分数和完成状态
        cmi_data = '{"cmi":{"completion_status":"completed","interactions":[],"launch_data":"","progress_measure":"1","score":{"scaled":"' + str(crate) + '","raw":"100"},"session_time":"0","success_status":"unknown","total_time":"0","mode":"normal"},"adl":{"data":[]},"cci":{"data":[],"service":{"dictionary":{"headword":"","short_cuts":""},"new_words":[],"notes":[],"writing_marking":[],"record":{"files":[]},"play":{"offline_media_id":"9999"}},"retry_count":"0","submit_time":""}}[INTERACTIONINFO]'
        data_set = {
            'action': 'setscoinfo',
            'cid': cid,
            'scoid': scoid,
            'uid': uid,
            'data': cmi_data,
            'isend': 'False'
        }
        session.post(scoUrl, data=data_set, headers=headers)
        
        # 3. 提交成绩落账
        data_save = {
            'action': 'savescoinfo160928',
            'cid': cid,
            'scoid': scoid,
            'uid': uid,
            'progress': '100',
            'crate': str(crate),
            'status': 'unknown',
            'cstatus': 'completed',
            'trycount': '0'
        }
        res_save = session.post(scoUrl, data=data_save, headers=headers)
        
        if res_save.ok and '"ret":0' in res_save.text:
            success += 1
            print(f'        >>>>>>>>>>>>>>正确率:{crate}%  完成!!!')
        else:
            fail += 1
            print(f'        >>>>>>>>>>>>>>正确率:{crate}%  失败!!!')
            
    return success, fail

def main():
    print('=================WELearn自动刷课脚本重构版===============')
    print('===========有问题请邮件联系wx:djxxpt2020===========')
    printline()
    
    session = init_login()
    printline()
    
    course_data = get_course_list(session)
    if not course_data:
        print('查询课程失败!!!')
        return

    print('查询课程成功!!!\n我的课程: \n')
    courses = course_data.get('clist', [])
    for i, course in enumerate(courses):
        print(f"[NO.{i:>2d}]  {course.get('name')}")
        
    try:
        order = int(input('\n请输入需要完成的课程序号（上方[]内的数字）: '))
        cid = courses[order].get('cid')
    except (ValueError, IndexError):
        print('序号输入不合法，退出程序!!')
        return
        
    print('获取单元中...')
    uid, classid, units = get_course_info(session, cid)
    if not units:
        print('未能获取单元列表。')
        return

    print('\n[NO. 0]  按顺序完成全部单元课程')
    for i, unit in enumerate(units):
        if unit.get('visible') == 'true':
            status = '[已开放]'
        else:
            status = '![未开放]!'
        print(f"[NO.{i+1:>2d}] {status}  {unit.get('unitname')}")

    try:
        unit_order = int(input('\n\n请选择需要完成的单元序号（上方[]内的数字，输入0为按顺序刷全部单元）： '))
    except ValueError:
        print('输入错误。退出！')
        return
        
    rate_mode_str = input("""
模式1:每个练习定正确率，请直接输入指定的正确率
如:希望每个练习正确率均为100，则输入 100

模式2:每个练习随机正确率，请输入正确率上下限并用英文逗号隔开
如:希望每个练习正确率为70,100

请严格按照以上格式输入每个练习的正确率: """)
    
    if ',' in rate_mode_str:
        try:
            r_min, r_max = map(int, rate_mode_str.split(','))
            from random import randint
            get_crate = lambda: randint(r_min, r_max)
        except:
            print('范围格式输入异常，使用默认 100')
            get_crate = lambda: 100
    else:
        try:
            val = int(rate_mode_str)
            get_crate = lambda: val
        except:
            print('格式异常，默认 100')
            get_crate = lambda: 100
            
    total_succ, total_fail = 0, 0
    target_units = units if unit_order == 0 else [units[unit_order - 1]]
    
    for unit in target_units:
        crate = get_crate()
        print(f"\n>>>> 开始处理单元: {unit.get('unitname')}")
        succ, fail = start_curr_spammer(session, cid, uid, classid, unit, crate)
        total_succ += succ
        total_fail += fail
        print('本单元运行完毕！')

    print(f"\n***************************************************\n全部完成!!\n总计:\n 成功: {total_succ}, 失败: {total_fail}\n")

if __name__ == '__main__':
    main()
