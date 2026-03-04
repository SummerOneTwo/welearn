import time
import threading
from common import init_login, get_course_list, printline
from welearn_curriculum import get_course_info

wrong = []

class NewThread(threading.Thread):
    def __init__(self, learntime, x, session, uid, cid):
        threading.Thread.__init__(self)
        self.daemon = True
        self.learntime = learntime
        self.x = x
        self.session = session
        self.uid = uid
        self.cid = cid

    def run(self):
        startstudy(self.learntime, self.x, self.session, self.uid, self.cid)

def startstudy(learntime, x, session, uid, cid):
    global wrong
    scoid = x['id']
    url = 'https://welearn.sflep.com/Ajax/SCO.aspx'
    
    headers = {
        'Referer': f'https://welearn.sflep.com/student/StudyCourse.aspx?cid={cid}'
    }
    
    # 尝试发第一包探查数据
    data1 = {'action': 'getscoinfo_v7', 'uid': uid, 'cid': cid, 'scoid': scoid}
    req1 = session.post(url, data=data1, headers=headers)
    
    # 如果学习数据不正确，初始化状态
    if '学习数据不正确' in req1.text:
        data_init = {'action': 'startsco160928', 'uid': uid, 'cid': cid, 'scoid': scoid}
        session.post(url, data=data_init, headers=headers)
        req1 = session.post(url, data=data1, headers=headers)
    
    if '学习数据不正确' in req1.text:
        print(f"\n错误:{x.get('location', '未知')}")
        wrong.append(x.get('location', '未知'))
        return 0

    try:
        back = req1.json()['comment']
        if 'cmi' in back:
            back = req1.json()
            cstatus = back.get('cmi', {}).get('completion_status', 'unknown')
            progress = back.get('cmi', {}).get('progress_measure', '0')
            session_time = back.get('cmi', {}).get('session_time', '0')
            total_time = back.get('cmi', {}).get('total_time', '0')
            crate = back.get('cmi', {}).get('score', {}).get('scaled', '')
        else:
            cstatus = 'not_attempted'
            progress = '0'
            session_time = '0'
            total_time = '0'
            crate = ''
    except:
        cstatus = 'not_attempted'
        progress = '0'
        session_time = '0'
        total_time = '0'
        crate = ''

    # 心跳循环
    print(f"\r已启动线程: {x.get('location', '未知')} [原始已学: {total_time}s]")
    for i in range(1, learntime + 1):
        time.sleep(1)
        if i % 60 == 0:
            # 每60秒上报一次
            data_keep = {
                'action': 'keepsco_with_getticket_with_updatecmitime',
                'uid': uid,
                'cid': cid,
                'scoid': scoid,
                'session_time': str(int(session_time) + i),
                'total_time': str(int(total_time) + i)
            }
            session.post(url, data=data_keep, headers=headers)
            print(f"\r线程: {x.get('location', '未知')} 当前秒数: {i}秒，总挂机: {int(total_time)+int(session_time)+i}秒")
            
    # 最终保存进度和时间
    data_save = {
        'action': 'savescoinfo160928',
        'cid': cid,
        'scoid': scoid,
        'uid': uid,
        'progress': progress,
        'crate': crate,
        'status': 'unknown',
        'cstatus': cstatus,
        'trycount': '0'
    }
    session.post(url, data=data_save, headers=headers)

def main():
    print('=================WELearn挂机时长脚本重构版===============')
    print('============有问题请联系wx:djxxpt2020==============')
    printline()
    
    session = init_login()
    printline()
    
    course_data = get_course_list(session)
    if not course_data:
        print('查询课程失败!!!')
        return

    courses = course_data.get('clist', [])
    for i, course in enumerate(courses):
        print(f"[id:{i:>2d}]  完成度 {course.get('per', 0):>2d}%  {course.get('name')}")
        
    try:
        order = int(input('\n请输入需要刷时长的课程id（id为上方[]内的序号）: '))
        cid = courses[order].get('cid')
    except (ValueError, IndexError):
        print('输入错误!!')
        return
        
    print('获取单元中...')
    uid, classid, units = get_course_info(session, cid)
    if not units:
        print('未能获取单元列表。')
        return

    print('\n\n[id: 0]  按顺序刷全部单元学习时长')
    for i, unit in enumerate(units):
        print(f"[id:{i+1:>2d}]    {unit.get('unitname')}")

    try:
        unit_order = int(input('\n\n请选择要刷时长的单元id（id为上方[]内的序号，输入0为刷全部单元）： '))
    except ValueError:
        print('输入错误。')
        return
        
    time_mode_str = input("""
模式1:每个练习增加指定学习时长，请直接输入时间
如:希望每个练习增加30秒，则输入 30

模式2:每个练习增加随机时长，请输入时间上下限并用英文逗号隔开
如:希望每个练习增加10,30

请严格按照以上格式输入: """)
    
    if ',' in time_mode_str:
        try:
            t_min, t_max = map(int, time_mode_str.split(','))
            from random import randint
            get_time = lambda: randint(t_min, t_max)
        except:
            print('范围格式异常，使用默认 60s')
            get_time = lambda: 60
    else:
        try:
            val = int(time_mode_str)
            get_time = lambda: val
        except:
            print('格式异常，使用默认 60s')
            get_time = lambda: 60
            
    target_units = units if unit_order == 0 else [units[unit_order - 1]]
    threads = []
    
    for unit in target_units:
        unitidx = unit.get('unitidx')
        ajaxUrl = f'https://welearn.sflep.com/ajax/StudyStat.aspx?action=scoLeaves&cid={cid}&uid={uid}&unitidx={unitidx}&classid={classid}'
        
        headers = {
            'Referer': f'https://welearn.sflep.com/Student/StudyCourse.aspx?cid={cid}'
        }
        
        try:
            leaves_res = session.get(ajaxUrl, headers=headers)
            sco_list = leaves_res.json().get('info', [])
        except Exception as e:
            print('获取sco列表报错:', e)
            continue
            
        for sco in sco_list:
            if sco.get('isvisible') == 'false':
                continue
            learntime = get_time()
            t = NewThread(learntime, sco, session, uid, cid)
            t.start()
            threads.append(t)
            time.sleep(0.5)  # 避免瞬间发包过快

    print('\n等待所有探查及保持线程退出…')
    for t in threads:
        t.join()

    print(f"\n\n运行结束!!\n累积出现未记录错误: {len(wrong)}个")
    if wrong:
        for i, idx in enumerate(wrong):
            print(f"第{i+1}个错误: {idx}")

if __name__ == '__main__':
    main()
