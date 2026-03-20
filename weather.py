import random

def get_weather_forecast():
    """
    Возвращает прогноз погоды на 24 часа.
    
    Returns:
        dict: Словарь с ключами hours, temperature, cloud_cover, wind_speed
    """
    # Список часов от 0 до 23
    hours = list(range(24))
    
    # Генерируем правдоподобные температуры
    # Температура выше днём и ниже ночью
    temperature = []
    for hour in hours:
        # Базовое значение: ночью холоднее (5-8°C), днём теплее (10-15°C)
        if 0 <= hour <= 5:  # Ночь и раннее утро
            base_temp = random.uniform(5, 8)
        elif 6 <= hour <= 8:  # Утро
            base_temp = random.uniform(7, 10)
        elif 9 <= hour <= 16:  # День
            base_temp = random.uniform(10, 15)
        else:  # Вечер
            base_temp = random.uniform(7, 11)
        
        # Добавляем небольшие случайные колебания
        temp = round(base_temp + random.uniform(-1, 1), 1)
        temperature.append(temp)
    
    # Генерируем облачность с учётом плавных изменений
    cloud_cover = []
    for hour in hours:
        # Делаем облачность более реалистичной с некоторой инерцией
        if hour == 0:
            cloud = random.randint(0, 100)
        else:
            # Вероятность резкого изменения облачности невелика
            if random.random() < 0.3:
                cloud = random.randint(0, 100)
            else:
                # Меняем облачность плавно
                cloud = cloud_cover[-1] + random.randint(-15, 15)
                cloud = max(0, min(100, cloud))
        cloud_cover.append(cloud)
    
    # Генерируем скорость ветра
    wind_speed = []
    for hour in hours:
        # Днём ветер может быть чуть сильнее
        if 9 <= hour <= 17:
            speed = round(random.uniform(1, 8), 1)
        else:
            speed = round(random.uniform(0, 6), 1)
        wind_speed.append(speed)
    
    return {
        "hours": hours,
        "temperature": temperature,
        "cloud_cover": cloud_cover,
        "wind_speed": wind_speed
    }

# Пример использования и вывода результата
if __name__ == "__main__":
    forecast = get_weather_forecast()
    
    print("Прогноз погоды на 24 часа:")
    print("-" * 70)
    
    # Выводим названия столбцов
    print(f"{'Время':<8} {'Температура':<12} {'   Облачность':<12} {'  Ветер':<10}")
    print("-" * 70)
    
    # Выводим данные в удобном формате
    for i in range(24):
        print(f"{forecast['hours'][i]:2d}:00      "
              f"{forecast['temperature'][i]:5.1f}°C       "
              f"{forecast['cloud_cover'][i]:3d}%          "
              f"{forecast['wind_speed'][i]:4.1f} м/с")
