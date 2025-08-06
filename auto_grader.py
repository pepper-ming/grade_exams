#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動化改考卷程式 - 完全自動化登入版本
使用selenium操作瀏覽器進行登入和批改作業
整合LLM API自動識別驗證碼
"""

import json
import time
import os
import base64
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class CaptchaResolver:
    """驗證碼解析器 - 支援Claude CLI和API兩種方式"""
    
    def __init__(self, config):
        self.config = config
        self.anthropic_client = None
        self.openai_client = None
        self.use_claude_cli = config.get('captcha', {}).get('use_claude_cli', True)  # 默認使用CLI
        
        # 從環境變數讀取API密鑰
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        # 初始化API客戶端（作為備用）
        if anthropic_key:
            self.anthropic_client = Anthropic(api_key=anthropic_key)
            
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        
        print(f"[INFO] 驗證碼識別方式: {'Claude CLI' if self.use_claude_cli else 'API'}")
    
    def save_captcha_image(self, image_data, filename):
        """儲存驗證碼圖片"""
        os.makedirs(self.config['captcha']['save_path'], exist_ok=True)
        filepath = os.path.join(self.config['captcha']['save_path'], filename)
        
        if isinstance(image_data, bytes):
            with open(filepath, 'wb') as f:
                f.write(image_data)
        else:
            image_data.save(filepath)
        
        print(f"驗證碼圖片已儲存: {filepath}")
        return filepath
    
    def image_to_base64(self, image_path):
        """將圖片轉換為base64編碼"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def recognize_captcha_with_anthropic(self, image_path):
        """使用Claude API識別驗證碼"""
        if not self.anthropic_client:
            return None
        
        try:
            image_base64 = self.image_to_base64(image_path)
            
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "請識別這個驗證碼圖片中的文字或數字。只回答驗證碼內容，不要其他說明。"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            )
            
            captcha_text = message.content[0].text.strip()
            print(f"Claude識別驗證碼: {captcha_text}")
            return captcha_text
            
        except Exception as e:
            print(f"Claude API識別失敗: {e}")
            return None
    
    def recognize_captcha_with_openai(self, image_path):
        """使用OpenAI API識別驗證碼（使用最划算的gpt-4o-mini模型）"""
        if not self.openai_client:
            return None
        
        try:
            image_base64 = self.image_to_base64(image_path)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 使用最划算的模型
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "請識別這個驗證碼圖片中的文字或數字。只回答驗證碼內容，不要其他說明。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=50  # 減少輸出token
            )
            
            captcha_text = response.choices[0].message.content.strip()
            print(f"GPT-4o-mini識別驗證碼: {captcha_text}")
            return captcha_text
            
        except Exception as e:
            print(f"OpenAI API識別失敗: {e}")
            return None
    
    def recognize_captcha_with_cli(self, image_path):
        """使用Claude CLI識別驗證碼"""
        try:
            # 構建識別prompt
            image_path = os.path.abspath(image_path)
            prompt = f'請使用Read工具讀取驗證碼圖片文件: "{image_path}" 然後識別其中的驗證碼內容。只回答驗證碼的數字或字母，不要其他說明。'
            
            # 調用Claude CLI
            import subprocess
            process = subprocess.Popen([
                'cmd', '/c', 'claude', 
                '--print', 
                '--output-format', 'text', 
                prompt
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='cp950',
            errors='replace',
            cwd=os.path.dirname(image_path)
            )
            
            stdout, stderr = process.communicate(timeout=45)
            
            if process.returncode == 0 and stdout.strip():
                # 解析回應
                import re
                response = stdout.strip()
                print(f"Claude CLI識別回應: {response}")
                
                # 驗證碼格式匹配
                patterns = [
                    r'\b[A-Z0-9]{4,6}\b',    # 4-6位大寫字母或數字
                    r'\b[0-9]{4,6}\b',       # 4-6位純數字  
                    r'\b[A-Za-z0-9]{3,8}\b'  # 3-8位混合
                ]
                
                excluded_words = {'read', 'tool', 'file', 'image', 'captcha', 'code', 'text'}
                
                for pattern in patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    for match in matches:
                        if match.lower() not in excluded_words:
                            print(f"Claude CLI識別驗證碼: {match}")
                            return match
                
                return None
            else:
                print(f"Claude CLI執行失敗: {stderr}")
                return None
                
        except Exception as e:
            print(f"Claude CLI識別失敗: {e}")
            return None

    def recognize_captcha(self, image_path):
        """識別驗證碼（按成本效益順序：Claude CLI > OpenAI > Anthropic）"""
        
        # 第一優先：Claude CLI（免費）
        if self.use_claude_cli:
            print("[INFO] 使用Claude CLI識別驗證碼（免費）...")
            result = self.recognize_captcha_with_cli(image_path)
            if result:
                return result
            print("[WARN] Claude CLI識別失敗，嘗試使用OpenAI API...")
        
        # 第二優先：OpenAI gpt-4o-mini（最划算的API）
        if self.openai_client:
            print("[INFO] 使用OpenAI gpt-4o-mini識別驗證碼（最划算）...")
            result = self.recognize_captcha_with_openai(image_path)
            if result:
                return result
            print("[WARN] OpenAI識別失敗，嘗試使用Anthropic API...")
        
        # 第三優先：Anthropic Claude（較貴的備援）
        if self.anthropic_client:
            print("[INFO] 使用Anthropic Claude識別驗證碼（備援）...")
            result = self.recognize_captcha_with_anthropic(image_path)
            if result:
                return result
            print("[ERROR] 所有識別方法都失敗了")
        
        return None

class AutoGrader:
    def __init__(self, config_file="config.json"):
        """初始化自動改考卷系統"""
        self.config = self.load_config(config_file)
        self.driver = None
        self.wait = None
        self.captcha_resolver = None
        
        if self.config:
            self.captcha_resolver = CaptchaResolver(self.config)
        
    def load_config(self, config_file):
        """載入配置檔案"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"找不到配置檔案: {config_file}")
            return None
        except json.JSONDecodeError:
            print(f"配置檔案格式錯誤: {config_file}")
            return None
    
    def setup_driver(self):
        """設置Chrome瀏覽器驅動"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 解決瀏覽器會話衝突問題
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--user-data-dir=C:\\temp\\chrome_user_data")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, self.config['settings']['timeout'])
            print("Chrome瀏覽器驅動設置成功")
            return True
        except Exception as e:
            print(f"瀏覽器驅動設置失敗: {e}")
            return False
    
    def capture_captcha_image(self):
        """抓取驗證碼圖片"""
        try:
            # 尋找驗證碼圖片元素
            captcha_img_selectors = [
                (By.XPATH, "//img[contains(@src, 'NewCode.php')]"),
                (By.CSS_SELECTOR, "img[src*='NewCode.php']")
            ]
            
            captcha_img = None
            for selector_type, selector_value in captcha_img_selectors:
                try:
                    captcha_img = self.driver.find_element(selector_type, selector_value)
                    print(f"找到驗證碼圖片: {selector_type} = {selector_value}")
                    break
                except:
                    continue
            
            if not captcha_img:
                print("無法找到驗證碼圖片元素")
                return None
            
            # 截取驗證碼圖片
            timestamp = int(time.time())
            filename = f"captcha_{timestamp}.png"
            os.makedirs(self.config['captcha']['save_path'], exist_ok=True)
            
            # 方法1：直接截取圖片元素
            try:
                filepath = os.path.join(self.config['captcha']['save_path'], filename)
                captcha_img.screenshot(filepath)
                print(f"驗證碼圖片截取成功: {filename}")
                return filepath
            except:
                pass
            
            # 方法2：通過圖片URL下載
            try:
                img_src = captcha_img.get_attribute('src')
                if img_src:
                    if img_src.startswith('data:image'):
                        # 處理base64圖片
                        header, data = img_src.split(',', 1)
                        img_data = base64.b64decode(data)
                        return self.captcha_resolver.save_captcha_image(img_data, filename)
                    else:
                        # 處理URL圖片
                        response = requests.get(img_src, cookies=self.get_browser_cookies())
                        if response.status_code == 200:
                            return self.captcha_resolver.save_captcha_image(response.content, filename)
            except Exception as e:
                print(f"下載驗證碼圖片失敗: {e}")
            
            return None
            
        except Exception as e:
            print(f"抓取驗證碼圖片時發生錯誤: {e}")
            return None
    
    def get_browser_cookies(self):
        """獲取瀏覽器cookies"""
        try:
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
            return cookies
        except:
            return {}
    
    def auto_login(self):
        """完全自動化登入"""
        if not self.config:
            print("配置檔案未載入")
            return False
        
        max_attempts = self.config['captcha']['max_attempts']
        
        for attempt in range(max_attempts):
            print(f"\n=== 登入嘗試 {attempt + 1}/{max_attempts} ===")
            
            try:
                # 訪問登入頁面
                login_url = self.config['login']['url']
                print(f"正在訪問登入頁面: {login_url}")
                self.driver.get(login_url)
                
                # 等待頁面載入
                time.sleep(self.config['settings']['wait_time'])
                
                # 等待模態框出現
                self.wait_for_modal()
                
                print("正在查找登入表單元素...")
                
                # 填寫帳號
                if not self.fill_username():
                    print("無法填寫帳號")
                    continue
                
                # 填寫密碼
                if not self.fill_password():
                    print("無法填寫密碼")
                    continue
                
                # 抓取並識別驗證碼
                captcha_image_path = self.capture_captcha_image()
                if not captcha_image_path:
                    print("無法抓取驗證碼圖片")
                    continue
                
                captcha_text = self.captcha_resolver.recognize_captcha(captcha_image_path)
                if not captcha_text:
                    print("無法識別驗證碼")
                    continue
                
                # 填寫驗證碼
                if not self.fill_captcha(captcha_text):
                    print("無法填寫驗證碼")
                    continue
                
                # 點擊登入按鈕
                if not self.click_login_button():
                    print("無法點擊登入按鈕")
                    continue
                
                # 等待登入結果
                time.sleep(self.config['settings']['wait_time'])
                
                # 檢查是否登入成功
                if self.check_login_success():
                    print("[SUCCESS] 登入成功！")
                    return True
                else:
                    print(f"登入失敗，第 {attempt + 1} 次嘗試")
                    
            except Exception as e:
                print(f"登入嘗試 {attempt + 1} 發生錯誤: {e}")
                
        print(f"經過 {max_attempts} 次嘗試後仍無法登入")
        return False
    
    def wait_for_modal(self):
        """等待登入模態框出現"""
        try:
            modal_selectors = [
                (By.ID, "sys_signin"),
                (By.CLASS_NAME, "modal")
            ]
            
            for selector_type, selector_value in modal_selectors:
                try:
                    modal = self.wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    print(f"[INFO] 找到登入模態框: {selector_type} = {selector_value}")
                    time.sleep(1)  # 等待模態框完全載入
                    return True
                except:
                    continue
            
            print("[INFO] 未找到模態框，繼續嘗試...")
            return True
        except Exception as e:
            print(f"[WARN] 等待模態框時發生錯誤: {e}")
            return True

    def fill_username(self):
        """填寫帳號"""
        username = os.getenv('LOGIN_USERNAME')
        if not username:
            print("[ERROR] 未設定LOGIN_USERNAME環境變數")
            return False
            
        selectors = [
            (By.ID, "UID"),
            (By.NAME, "UID"),
            (By.CSS_SELECTOR, "input[name='UID']")
        ]
        
        for selector_type, selector_value in selectors:
            try:
                username_field = self.driver.find_element(selector_type, selector_value)
                if username_field.is_displayed() and username_field.is_enabled():
                    username_field.clear()
                    username_field.send_keys(username)
                    print(f"[PASS] 已填寫帳號: {username} (使用: {selector_value})")
                    return True
            except:
                continue
        return False
    
    def fill_password(self):
        """填寫密碼"""
        password = os.getenv('LOGIN_PASSWORD')
        if not password:
            print("[ERROR] 未設定LOGIN_PASSWORD環境變數")
            return False
            
        password_selectors = [
            (By.ID, "PWD"),
            (By.NAME, "PWD"),
            (By.CSS_SELECTOR, "input[name='PWD']")
        ]
        
        for selector_type, selector_value in password_selectors:
            try:
                password_field = self.driver.find_element(selector_type, selector_value)
                if password_field.is_displayed() and password_field.is_enabled():
                    password_field.clear()
                    password_field.send_keys(password)
                    print(f"[PASS] 已填寫密碼 (使用: {selector_value})")
                    return True
            except:
                continue
        return False
    
    def fill_captcha(self, captcha_text):
        """填寫驗證碼"""
        captcha_selectors = [
            (By.ID, "NewCode"),
            (By.NAME, "NewCode"),
            (By.CSS_SELECTOR, "input[name='NewCode']")
        ]
        
        for selector_type, selector_value in captcha_selectors:
            try:
                captcha_field = self.driver.find_element(selector_type, selector_value)
                if captcha_field.is_displayed() and captcha_field.is_enabled():
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_text)
                    print(f"[PASS] 已填寫驗證碼: {captcha_text} (使用: {selector_value})")
                    return True
            except:
                continue
        return False
    
    def click_login_button(self):
        """點擊登入按鈕"""
        button_selectors = [
            (By.XPATH, "//button[@type='submit' and contains(@class, 'btn')]"),
            (By.XPATH, "//button[contains(text(), '登入')]"),
            (By.CSS_SELECTOR, "button[type='submit']")
        ]
        
        for selector_type, selector_value in button_selectors:
            try:
                login_button = self.driver.find_element(selector_type, selector_value)
                if login_button.is_displayed() and login_button.is_enabled():
                    login_button.click()
                    print(f"[PASS] 已點擊登入按鈕 (使用: {selector_value})")
                    return True
            except:
                continue
        return False
    
    def check_login_success(self):
        """檢查是否登入成功"""
        try:
            current_url = self.driver.current_url
            print(f"當前URL: {current_url}")
            
            # 檢查是否還在登入頁面
            if "signOut" in current_url:
                return False
            
            # 檢查是否到達教師頁面
            if "teacher" in current_url:
                return True
                
            return True
            
        except Exception as e:
            print(f"檢查登入狀態時發生錯誤: {e}")
            return False
    
    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            print("瀏覽器已關閉")

def main():
    """主程序"""
    print("=== 自動化改考卷程式 v2.0 ===")
    print("支援自動驗證碼識別功能")
    
    grader = AutoGrader()
    
    if not grader.setup_driver():
        print("無法設置瀏覽器驅動")
        return
    
    try:
        if grader.auto_login():
            print("系統登入成功，可以開始批改作業")
            # 在這裡添加批改考卷的功能
            input("按Enter鍵關閉程序...")
        else:
            print("自動登入失敗")
    
    except KeyboardInterrupt:
        print("程序被用戶中斷")
    
    finally:
        grader.close()

if __name__ == "__main__":
    main()