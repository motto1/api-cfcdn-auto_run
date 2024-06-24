import requests
import csv
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

api_token = ""
zone_id = ""
domain = ""  # 您的二级域名

# Cloudflare API 端点
api_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# 创建会话，并设置重试策略
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)

# 通用的请求函数，带重试机制和超时设置
def make_request(method, url, **kwargs):
    try:
        response = session.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"请求错误：{e}")
        if 'json' in kwargs:
            print(f"请求数据: {kwargs['json']}")
        return None

# 获取所有指定二级域名下的 DNS 记录
def get_dns_records():
    response = make_request("GET", api_url, headers=headers, params={"name": domain})
    if response:
        result = response.json()
        return result["result"]
    else:
        return []

# 删除指定二级域名下的所有 DNS 记录
def delete_dns_records(dns_records):
    for record in dns_records:
        record_id = record["id"]
        delete_response = make_request("DELETE", f"{api_url}/{record_id}", headers=headers)
        if delete_response:
            print(f"已删除 DNS 记录: {record_id}")

# 下载数据并保存到 CSV
def download_and_save_csv(url, save_path):
    response = make_request("POST", url, json={"key": "o1zrmHAF"})
    if response:
        result = response.json()
        if result["code"] == 200:
            with open(save_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["节点类别", "IP地址", "线路", "节点", "延迟", "下载速度", "时间"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for category, ips in result["info"].items():
                    for ip_info in ips:
                        delay_str = ip_info["delay"].replace("ms", "")
                        try:
                            delay = float(delay_str)
                            if category == "CT":
                                writer.writerow({
                                    "节点类别": category,
                                    "IP地址": ip_info["ip"],
                                    "线路": ip_info["line"],
                                    "节点": ip_info["node"],
                                    "延迟": delay,
                                    "下载速度": ip_info["downloadspeed"],
                                    "时间": ip_info["time"]
                                })
                                add_dns_record(ip_info["ip"])
                        except ValueError:
                            print(f"无法转换延迟值为浮点数：{ip_info['delay']}")
            print("已将延迟不高于100的数据保存到 ip.csv 文件中")
        else:
            print("请求失败，错误信息：{}".format(result['info']))
    else:
        print("请求失败，状态码：{}".format(response.status_code))

# 添加 DNS 记录
def add_dns_record(ip_address):
    data = {
        "type": "A",
        "name": domain,
        "content": ip_address,
        "ttl": 1,
        "proxied": False
    }
    response = make_request("POST", api_url, headers=headers, json=data)
    if response:
        print(f"IP地址 {ip_address} 已成功解析到Cloudflare域名下")
    else:
        print(f"解析IP地址 {ip_address} 时出错")

# 主逻辑
def main():
    try:
        dns_records = get_dns_records()
        if dns_records:
            delete_dns_records(dns_records)
        else:
            print("没有找到DNS记录")
        
        download_and_save_csv("https://api.345673.xyz/get_data", "ip.csv")
    except Exception as e:
        print(f"执行过程中发生错误：{e}")

if __name__ == "__main__":
    main()
