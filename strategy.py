# strategy.py
# strategy.py

import sys
from typing import Dict, List, Optional, Any


def optimal_bidding_strategy(
    generation_data: Optional[Dict[int, Dict[str, float]]] = None,
    cost_data: Optional[Dict[int, Dict[str, float]]] = None,
    demand: float = 1000.0,
) -> Dict[str, Any]:
    """
    Жадный алгоритм закупки электроэнергии для покрытия заданного спроса.

    Параметры:
        generation_data: почасовая выработка вида
            {час: {'wind': float, 'solar': float}, ...}, часы 0..23.
            Если None, загружается из generation.get_generation_table().
        cost_data: почасовые цены покупки 1 кВт у каждого источника,
            вида {час: {'wind': float, 'solar': float}, ...}.
            Если None, вычисляется через cost.calculate_cost().
        demand: требуемое количество энергии (кВт).

    Возвращает:
        dict: {
            'total_cost': float,
            'purchases': list[dict],
            'unmet_demand': float
        }
    """
    # ----- 1. Получение generation_data -----
    if generation_data is None:
        try:
            from generation import get_generation_table
            raw_gen = get_generation_table()
        except ImportError:
            raise ImportError(
                "Модуль generation.py не найден или не содержит функцию get_generation_table()"
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка при получении данных генерации: {e}")

        # Приведение к формату {час: {'wind': ..., 'solar': ...}}
        if isinstance(raw_gen, dict):
            # Если raw_gen содержит списки "solar" и "wind"
            if "solar" in raw_gen and "wind" in raw_gen and isinstance(raw_gen["solar"], list):
                generation_data = {}
                for hour in range(24):
                    generation_data[hour] = {
                        "solar": raw_gen["solar"][hour],
                        "wind": raw_gen["wind"][hour],
                    }
            # Если raw_gen уже в нужном формате (ключи - часы)
            elif all(isinstance(k, int) for k in raw_gen.keys()):
                generation_data = raw_gen
            else:
                raise ValueError("Неподдерживаемый формат generation_data")
        else:
            raise ValueError("get_generation_table() вернул не словарь")

    # ----- 2. Получение cost_data -----
    if cost_data is None:
        try:
            # Пытаемся получить weather_data из generation.py
            try:
                from generation import get_weather_data
                weather_data = get_weather_data()
            except (ImportError, AttributeError):
                # Если функции нет, используем пустой словарь (может вызвать ошибку в calculate_cost)
                weather_data = {}

            from cost import calculate_cost

            # Подготавливаем generation_data в формате, ожидаемом calculate_cost
            gen_for_cost = {
                "solar": [generation_data[h]["solar"] for h in range(24)],
                "wind": [generation_data[h]["wind"] for h in range(24)],
            }

            cost_result = calculate_cost(weather_data, gen_for_cost)

            # Извлекаем суточные себестоимости (одинаковые для всех часов)
            solar_cost = cost_result.get("solar", float("inf"))
            wind_cost = cost_result.get("wind", float("inf"))

            # Формируем почасовые цены (одинаковые для всех часов)
            cost_data = {}
            for hour in range(24):
                cost_data[hour] = {
                    "wind": wind_cost,
                    "solar": solar_cost,
                }
        except ImportError:
            raise ImportError(
                "Модуль cost.py не найден или не содержит функцию calculate_cost()"
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка при получении данных о ценах: {e}")

    # ----- 3. Жадный алгоритм закупки -----
    lots = []  # (price, amount, hour, source)
    for hour in range(24):
        for source in ("wind", "solar"):
            amount = generation_data[hour].get(source, 0.0)
            price = cost_data[hour].get(source, float("inf"))
            if amount > 0 and price < float("inf"):
                lots.append((price, amount, hour, source))

    # Сортируем по цене (дешёвые первыми)
    lots.sort(key=lambda x: x[0])

    remaining = demand
    total_cost = 0.0
    purchases = []

    for price, amount, hour, source in lots:
        if remaining <= 0:
            break
        take = min(amount, remaining)
        total_cost += take * price
        purchases.append(
            {
                "hour": hour,
                "source": source,
                "amount": take,
                "price": price,
            }
        )
        remaining -= take

    return {
        "total_cost": total_cost,
        "purchases": purchases,
        "unmet_demand": remaining,
    }


def main() -> None:
    """Пример использования."""
    try:
        result = optimal_bidding_strategy(demand=1000)

        print("=== Результат закупки ===")
        print(f"Общая стоимость: {result['total_cost']:.2f} руб.")
        print(f"Непокрытый спрос: {result['unmet_demand']:.2f} кВт\n")

        if result["purchases"]:
            print("Детали покупок:")
            for p in result["purchases"]:
                print(
                    f"  час {p['hour']:2d} | {p['source']:5s} | "
                    f"{p['amount']:6.2f} кВт по {p['price']:6.2f} руб/кВт"
                )
        else:
            print("Покупок не совершено.")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
pass
