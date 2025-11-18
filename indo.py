import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time


def read_accounts(file_path):
    accounts = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                profile_id, wallet_address = line.strip().split(',')
                accounts.append({"profile_id": profile_id, "wallet_address": wallet_address})
        return accounts
    except Exception as e:
        print(f"Ошибка при чтении файла accounts.txt: {str(e)}")
        return []


def save_result(wallet_address, status):
    """Сохраняет результат выполнения в results.txt"""
    try:
        with open("results.txt", "a") as file:
            file.write(f"{wallet_address}: {status}\n")
        print(f"Результат сохранён: {wallet_address}: {status}")
    except Exception as e:
        print(f"Ошибка при сохранении результата: {str(e)}")


def open_adspower_profile(profile_id, api_key, api_url="http://local..."):
    params = {"user_id": profile_id}
    if api_key:
        params["api_key"] = api_key
    try:
        response = requests.get(f"{api_url}/api/v1/browser/start", params=params, timeout=10)
        response_data = response.json()
        if response_data["code"] == 0:
            return response_data["data"]["webdriver"], response_data["data"]["ws"]["selenium"]
        else:
            print(f"Ошибка API AdsPower для профиля {profile_id}: {response_data['msg']}")
            return None, None
    except Exception as e:
        print(f"Ошибка соединения с API для профиля {profile_id}: {str(e)}")
        return None, None


def send_telegram_message(profile_id, wallet_address, api_key, api_url="http://local..."):
    # Инициализируем статус как неуспешный
    status = "failed"

    # Открываем профиль через API
    webdriver_path, ws_url = open_adspower_profile(profile_id, api_key, api_url)
    if not webdriver_path or not ws_url:
        save_result(wallet_address, status)
        return

    # Настройка Selenium для подключения к открытому браузеру
    driver = None
    try:
        service = Service(webdriver_path)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", ws_url)
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Ошибка инициализации ChromeDriver для профиля {profile_id}: {str(e)}")
        save_result(wallet_address, status)
        return

    try:
        # Открываем страницу Telegram
        driver.get("https://web.telegram.org/k/укажи")

        # Ждем, пока поле ввода станет видимым и активным
        input_field = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']"))
        )

        # Прокручиваем к элементу и кликаем для активации
        driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
        input_field.click()

        # Формируем сообщение
        message = f"/faucet {wallet_address}"

        # Вводим сообщение и отправляем
        input_field.send_keys(message)
        input_field.send_keys(Keys.ENTER)

        print(f"Сообщение отправлено для кошелька: {wallet_address}")

        # Отмечаем успех, если сообщение отправлено
        status = "success"

        # Ждём 3 секунды
        time.sleep(3)

        # Закрываем вкладку Telegram
        try:
            driver.close()
        except:
            pass  # Игнорируем ошибки закрытия вкладки

        # Открываем новую чистую вкладку
        try:
            driver.switch_to.new_window('tab')
            driver.get("about:blank")
            time.sleep(1)
        except:
            pass  # Игнорируем ошибки открытия вкладки

    except Exception as e:
        print(f"Ошибка для профиля {profile_id}: {str(e)}")

    finally:
        # Сохраняем результат
        save_result(wallet_address, status)

        # Закрываем браузер
        if driver:
            try:
                driver.quit()
            except:
                pass  # Игнорируем ошибки закрытия браузера

        # Закрываем профиль через API
        try:
            params = {"user_id": profile_id}
            if api_key:
                params["api_key"] = api_key
            requests.get(f"{api_url}/api/v1/browser/stop", params=params, timeout=10)
            print(f"Профиль {profile_id} закрыт")
        except:
            print(f"Не удалось закрыть профиль {profile_id} через API")


# Основной код
if __name__ == "__main__":
    # Укажите ваш API-ключ (если требуется, иначе оставьте пустым)
    API_KEY = ""  # Замените на ваш API-ключ, например "abc123xyz789"
    API_URL = "http://local..."  # Ваш адрес API

    # Читаем аккаунты из файла
    accounts = read_accounts("accounts.txt")

    if not accounts:
        print("Не удалось загрузить аккаунты. Проверьте файл accounts.txt.")
    else:
        for account in accounts:
            send_telegram_message(
                profile_id=account["profile_id"],
                wallet_address=account["wallet_address"],
                api_key=API_KEY,
                api_url=API_URL
            )
            # Задержка между аккаунтами
            time.sleep(5)