from flask import Flask, render_template, url_for, redirect, request
import folium
from folium.plugins import MarkerCluster
import sys
import mysql.connector
import random
import time
import os
import io


# 允许上传的文件扩展名（可选）
ALLOWED_EXTENSIONS = {'txt', 'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



print("程序开始")
# 创建数据库连接
def connect(retry_num): #retry_num:记录重试次数，连接失败后会重试连接，默认最多五次
    if(retry_num<=0):
        return -1
    try:
        global db,cursor
        db = mysql.connector.connect(
            host="db-icg.dev.lianyoushixun.com",  # MySQL服务器地址
            user="customer_location",  # 用户名
            password="abPACbBT_vDjrWcFZW2!VoBUjyAaU7d8",  # 密码
            database="customer_location"  # 数据库名称
        )
        print("数据库登陆成功")  # 若此处仍崩溃，问题在连接本身
        # 创建游标对象，用于执行SQL查询
        cursor = db.cursor()
        return
    except Exception as e:
        print(f"连接失败: {e}")
        connect(retry_num-1)

connect(5)
def element_in_column(data, i, target):#验证某元素是否在某多维列表第二下标为i的位置
    return any(len(row) > i and row[i] == target for row in data)

crisisgoClient_list, potentialCrisisgoClient_list, E911Client_list, psapClient_list, potentialPsapClient_list = [], [], [], [], [] #存储用户状态数据
def refreshClient():
    global crisisgoClient_list, potentialCrisisgoClient_list, E911Client_list, psapClient_list,potentialPsapClient_list, client_dic
    #从数据库提取/更新客户数据
    cursor.execute("SELECT * FROM crisisgoClient")
    crisisgoClient_list=cursor.fetchall()
    cursor.execute("SELECT * FROM potentialCrisisgoClient")
    potentialCrisisgoClient_list=cursor.fetchall()
    cursor.execute("SELECT * FROM E911Client")
    E911Client_list=cursor.fetchall()
    cursor.execute("SELECT * FROM psapClient")
    psapClient_list=cursor.fetchall()
    cursor.execute("SELECT * FROM potentialPsapClient")
    potentialPsapClient_list = cursor.fetchall()
    print(potentialPsapClient_list)###
    #存储客户相关列表,格式与数据库相同，用于客户类型筛选
    client_dic={
        "crisisgoClient":crisisgoClient_list,
        "E911Client":E911Client_list,
        "potentialCrisisgoClient":potentialCrisisgoClient_list,
        "psapClient":psapClient_list,
        "potentialPsapClient":potentialPsapClient_list
    }



def customerSegment_check(customerSegment,id,idSub): #idSub为id类型对应下标(在用户类型数据cdv表中的横向位置，0开始)
    flag=[]
    for customerSegment_i in customerSegment:
        if not customerSegment_i=="noneClient":  #正常类型
            #print([customerSegment_i,idSub,id,client_dic[customerSegment_i],element_in_column(client_dic[customerSegment_i],idSub,id)])###
            if element_in_column(client_dic[customerSegment_i],idSub,id):
                flag.append(customerSegment_i)
        else:
            if (not customerSegment_check(["crisisgoClient"],id,idSub)) and\
            (not customerSegment_check(["E911Client"],id,idSub)) and\
            (not customerSegment_check(["potentialCrisisgoClient"],id,idSub)) and\
            (not customerSegment_check(["psapClient"],id,idSub)) and\
            (not customerSegment_check(["potentialPsapClient"],id,idSub)):
                flag.append('noneClient')
                #noneClient: 都不在
    return flag



#后端Flask区域：
app = Flask(__name__)

@app.route('/update_data',methods=['POST'])
def update_data():
    print("进入文件处理")
    db.ping(reconnect=True,attempts=5)
    upList=None  #待上传数据
    upType=None  #待上传类型
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        print("222222")###
        return render_template("upload_error.html",msg='No File Selected')
    
    file = request.files['file']
    upType = request.form.get("upType")
    # 如果用户没有选择文件，浏览器提交的文件名可能为空字符串
    if file.filename == '':
        print(3333333333)###
        return render_template("upload_error.html",msg='No File Selected')
    
    if file and allowed_file(file.filename):
        #开始处理上传数据
        print(upType)
        file_stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        print("fp1")###
        next(file_stream)
        print("fp2")###
        cursor.execute(f"DELETE FROM {upType}")
        print("fp3")###
        for line in file_stream:
            print("在循环中")###
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) > 5:
                print(f"跳过无效行: {line}")
                continue
            ncessch,ppin,psap_uuid,leaid,name=parts
            cursor.execute("SELECT * FROM public_schools WHERE ncessch = %s",(ncessch,))
            r=cursor.fetchone()
            if not r:
                ncessch=None#处理错误数据，不写入数据库
                cursor.execute("SELECT * FROM private_schools WHERE ppin = %s ",(ppin,))
                r=cursor.fetchone()
                if not r:
                    ppin=None
                    cursor.execute("SELECT * FROM psap_info WHERE psap_uuid = %s",(psap_uuid,))
                    r=cursor.fetchone()
                    if not r:
                        psap_uuid=None
                        cursor.execute("SELECT * FROM school_districts WHERE leaid = %s",(leaid,))
                        r=cursor.fetchone()
                        if not r:
                            leaid=None
                            print("错误记录")
                            continue
            print("在记录中")
            try:
                #执行插入数据
                cursor.execute(
                    f"INSERT INTO {upType} (ncessch,ppin,psap_uuid,leaid) VALUES (%s,%s,%s,%s)",
                    (ncessch,ppin,psap_uuid,leaid)
                )
                
            except Exception as e:
                print(f"插入错误: {e}")
        db.commit()
        return redirect('/')
    else:
        return render_template("upload_error.html",msg='Please choose csv/txt files!')



@app.route('/')
def home():
    print("进入主页")
    return redirect('map?state=AL&siteType=private&siteType=psap&siteType=district&customerSegment=crisisgoClient&customerSegment=potentialCrisisgoClient&customerSegment=E911Client&customerSegment=psapClient')
    



@app.route('/map')
def map():
    print("进入map页面")
    db.ping(reconnect=True,attempts=5)
    refreshClient()#更新数据库
    state=request.args.get('state')
    siteType=request.args.getlist('siteType')
    customerSegment=request.args.getlist('customerSegment')
    print("正在处理异常值")###
    #处理异常值
    if(state==None):
        state='Any'
    if(siteType==None):
        siteType=[]
    if(customerSegment==None):
        customerSegment=[]



    print(state,siteType,customerSegment)#打印Get的数据
    # 处理“州”的查询
    states = []
    us_regions = {
    "Northeast": [
        "CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"
    ],
    "Midwest": [
        "IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"
    ],
    "South": [
        "AL", "AR", "DE", "FL", "GA", "KY", "LA", "MD", "MS", "NC", "OK",
        "SC", "TN", "TX", "VA", "WV"
    ],
    "West": [
        "AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY"
    ]
    }

    if(state not in ("West","South","Midwest","Northeast")):
        if(state=='Any'):
            states.extend(us_regions["West"]+us_regions["South"]+us_regions["Midwest"]+us_regions["Northeast"])
        else:
            states.append(state)
    else:
        states.extend(us_regions[state])
    print(states)
    # 创建占位符字符串，比如 (%s, %s, %s, %s)
    placeholders = ', '.join(['%s'] * len(states))

    m = folium.Map(location=[38.9023, -77.0371], zoom_start=2,max_zoom=18)#地图初始化
    marker_cluster=MarkerCluster(
        options={
        'maxClusterRadius': 40  # Smaller = more clusters split apart sooner
        }
    ).add_to(m)

    #marker_cluster=m
    
    points=[]



    #定义“图标”字典
    icon_private={
        "noneClient":folium.CustomIcon(
            icon_image="static/icons/private_none.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "crisisgoClient":folium.CustomIcon(
            icon_image="static/icons/private_crisisgo.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "E911Client":folium.CustomIcon(
            icon_image="static/icons/private_e911.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "potentialCrisisgoClient":folium.CustomIcon(
            icon_image="static/icons/private_potential.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
    }

    icon_public={
        "noneClient":folium.CustomIcon(
            icon_image="static/icons/public_none.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "crisisgoClient":folium.CustomIcon(
            icon_image="static/icons/public_crisisgo.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "E911Client":folium.CustomIcon(
            icon_image="static/icons/public_e911.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "potentialCrisisgoClient":folium.CustomIcon(
            icon_image="static/icons/public_potential.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
    }

    icon_district={
        "noneClient":folium.CustomIcon(
            icon_image="static/icons/district_none.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "crisisgoClient":folium.CustomIcon(
            icon_image="static/icons/district_crisisgo.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "E911Client":folium.CustomIcon(
            icon_image="static/icons/district_e911.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "potentialCrisisgoClient":folium.CustomIcon(
            icon_image="static/icons/district_potential.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
    }

    icon_psap={
        "psapClient":folium.CustomIcon(
            icon_image="static/icons/police_client.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "noneClient":folium.CustomIcon(
            icon_image="static/icons/police_none.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
        "potentialPsapClient":folium.CustomIcon(
            icon_image="static/icons/police_potential.png",
            icon_size=(50,50),
            icon_anchor=(25,50)
        ),
    }
    
    if("private" in siteType):
        print("选择州")
        if(states!=[]):
            #选择州
            print("数据库连接前")
            cursor.execute(f"SELECT * FROM private_schools WHERE state IN ({placeholders})",states)
            print("数据库连接后")
        temp_list=cursor.fetchall()#temp_list存储选择的所有学校数据\
        print("进入添加点循环")###
        for i in temp_list:
            segmentType=customerSegment_check(customerSegment=customerSegment,id=i[1],idSub=0)#如果符合客户类型条件
                #print("符合条件，添加点中")###
            if(not segmentType==[]):
                points.append([float(i[11]),float(i[12])])
                if("E911Client" in segmentType):
                    folium.Marker([i[11], i[12]], popup=i[2],icon=icon_private["E911Client"]).add_to(marker_cluster)#添加标点
                else:
                    try:
                        folium.Marker([i[11], i[12]], popup=i[2],icon=icon_private[segmentType[0]]).add_to(marker_cluster)#添加标点
                    except:
                        print("error")
        print("退出添加点循环")###


    print("进入处理public")###
    #选择Public Schools
    if("public" in siteType):
        if(states!=[]):
            #选择州
            cursor.execute(f"SELECT * FROM public_schools WHERE state IN ({placeholders})",states)
        temp_list=cursor.fetchall()#temp_list存储选择的所有学校数据
        for i in temp_list:
            segmentType=customerSegment_check(customerSegment=customerSegment,id=i[1],idSub=1)#如果符合客户类型条件
                #print("符合条件，添加点中")###
            if(not segmentType==[]):#如果符合客户类型条件
                print("符合条件，添加点中")###
                points.append([float(i[13]),float(i[14])])
                if("E911Client" in segmentType):
                    folium.Marker([i[13], i[14]], popup=i[3],icon=icon_public["E911Client"]).add_to(marker_cluster)#添加标点
                else:
                    try:
                        folium.Marker([i[13], i[14]], popup=i[3],icon=icon_public[segmentType[0]]).add_to(marker_cluster)#添加标点
                    except:
                        print("error")
            

    #选择PSAP
    print("进入处理psap")###
    if("psap" in siteType):
        if(states!=[]):
            #选择州
            cursor.execute(f"SELECT * FROM psap_info WHERE state IN ({placeholders})",states)
        temp_list=cursor.fetchall()#temp_list存储选择的所有学校数据，但是这一步会消耗最多15秒时间
        
        for i in temp_list:
            if(i[8]==i[7]==0):
                print(i[2]+" is in unknown position")
                continue
            segmentType=customerSegment_check(customerSegment=customerSegment,id=i[1],idSub=2)#如果符合客户类型条件
                #print("符合条件，添加点中")###
            if not segmentType==[]:#如果符合客户类型条件
                print("符合条件，添加点中")###
                points.append([float(i[8]),float(i[7])])
                try:
                    folium.Marker([i[8], i[7]], popup=i[2],icon=icon_psap[segmentType[0]]).add_to(marker_cluster)#添加标点
                except:
                    print("error")

    #选择school_district
    print("进入处理school_district")###
    if("district" in siteType):
        if(states!=[]):
            #选择州
            cursor.execute(f"SELECT * FROM school_districts WHERE state IN ({placeholders})",states)
        temp_list=cursor.fetchall()#temp_list存储选择的所有学校数据
        for i in temp_list:
            segmentType=customerSegment_check(customerSegment=customerSegment,id=i[3],idSub=3)#如果符合客户类型条件
                #print("符合条件，添加点中")###
            if not segmentType==[]:#如果符合客户类型条件
                print("符合条件，添加点中")###
                points.append([float(i[1]),float(i[0])])
                if("E911Client" in segmentType):
                    folium.Marker([i[1], i[0]], popup=i[4],icon=icon_district["E911Client"]).add_to(marker_cluster)#添加标点
                else:
                    try:
                        folium.Marker([i[1], i[0]], popup=i[4],icon=icon_district[segmentType[0]]).add_to(marker_cluster)#添加标点
                    except:
                        print("error")





    m.fit_bounds(points)
    start_time = time.time()
    mapHtml=m.get_root().render()
    end_time = time.time()
    print(end_time - start_time)
    
    return render_template('map.html',html_map=mapHtml,state=state,siteType=siteType,customerSegment=customerSegment)#传递上一次用户的选项


if __name__ == '__main__':
    app.run(debug=True) 