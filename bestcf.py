import requests
import csv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Cloudflare API 参数
api_token = ""
zone_id = ""
subdomain = ""  # 您的二级域名

# Cloudflare API 端点
api_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

# 请求标头
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# 创建一个会话对象，增加重试机制
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

try:
    # 发送GET请求以获取所有指定二级域名下的DNS记录
    response = session.get(api_url, headers=headers, params={"name": subdomain})
    response.raise_for_status()
    
    # 解析JSON响应
    data = response.json()
    
    # 遍历每个DNS记录并删除它们
    for record in data['result']:
        record_id = record['id']
            
        # 构造删除记录的API端点
        delete_url = f"{api_url}/{record_id}"
            
        # 发送DELETE请求以删除记录
        delete_response = session.delete(delete_url, headers=headers)
        delete_response.raise_for_status()
            
        # 检查删除记录的响应状态码
        if delete_response.status_code == 200:
            print(f"已成功删除DNS记录：{record['name']} - {record['content']}")
        else:
            print(f"删除DNS记录时出错：{delete_response.text}")

    # 删除完毕后，您可以继续添加新的记录
    # 定义文件URL和保存路径
    url = "https://raw.githubusercontent.com/ymyuuu/IPDB/main/bestcf.txt"
    save_path = "bestcf.csv"

    # 发送GET请求到URL
    response = session.get(url)
    response.raise_for_status()

    # 解码响应内容为文本
    content = response.text
        
    # 将内容分割成行
    lines = content.splitlines()
        
    # 以写入模式打开CSV文件
    with open(save_path, 'w', newline='', encoding='utf-8') as csvfile:
        # 创建CSV写入器对象
        csv_writer = csv.writer(csvfile)
            
        # 遍历每一行
        for line in lines:
            # 通过空格分割行
            data = line.split()
                
            # 将数据写入CSV文件
            csv_writer.writerow(data)
        
    print("数据已保存到", save_path)
        
    # 从CSV文件中读取IP地址并解析到Cloudflare域名下
    with open(save_path, 'r', newline='', encoding='utf-8') as csvfile:
        # 创建CSV读取器对象
        csv_reader = csv.reader(csvfile)
            
        # 跳过标题行（如果有的话）
        next(csv_reader)
            
        # 读取每一行数据
        for row in csv_reader:
            ip_address = row[0]  # 假设IP地址在第一列
                
            # 请求主体
            data = {
                "type": "A",
                "name": subdomain,
                "content": ip_address,
                "ttl": 1,  # TTL（生存时间），以秒为单位
                "proxied": False  # 关闭 Cloudflare 代理
            }

            # 发送POST请求以创建DNS记录
            response = session.post(api_url, headers=headers, json=data)
            response.raise_for_status()

            # 检查响应状态码
            if response.status_code == 200:
                print(f"IP地址 {ip_address} 已成功解析到 Cloudflare 域名下")
            else:
                print(f"解析IP地址 {ip_address} 时出错：{response.text}")

except requests.exceptions.RequestException as e:
    print(f"请求出错：{e}")

