"""Cost calculation for renewable generation based on weather conditions."""

import random
from typing import Dict, List, Optional, Sequence


SOLAR_BASE_COST = 0.06
SOLAR_TEMP_OPTIMAL = 25.0
SOLAR_TEMP_PENALTY = 0.004

WIND_BASE_COST = 0.05
WIND_WEAR_THRESHOLD = 12.0
WIND_WEAR_PENALTY = 0.02

_HOURS_IN_DAY = 24
_CONSUMPTION_KEYS = ("consumption", "demand", "load", "consumer_usage")
PRICE_MIN_PER_KWH = 0.04
PRICE_MAX_PER_KWH = 0.14


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_dict(data: object, name: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dictionary.")


def _require_list_of_numbers(values: object, field_name: str, *, length: int) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    if len(values) != length:
        raise ValueError(f"{field_name} must contain exactly {length} items.")
    if not all(_is_number(item) for item in values):
        raise ValueError(f"{field_name} must contain only numeric values.")


def _require_keys(data: dict, required_keys: Sequence[str], data_name: str) -> None:
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"{data_name} is missing required keys: {', '.join(missing_keys)}.")


def _require_non_negative(values: Sequence[float], field_name: str) -> None:
    if any(item < 0 for item in values):
        raise ValueError(f"{field_name} must contain only non-negative values.")


def _validate_weather_data(weather_data: dict) -> None:
    _require_dict(weather_data, "weather_data")
    required_keys = ("hours", "temperature", "cloud_cover", "wind_speed")
    _require_keys(weather_data, required_keys, "weather_data")

    for key in required_keys:
        _require_list_of_numbers(weather_data[key], f"weather_data['{key}']", length=_HOURS_IN_DAY)

    expected_hours = list(range(_HOURS_IN_DAY))
    hours = weather_data["hours"]
    if hours != expected_hours:
        raise ValueError("weather_data['hours'] must be exactly [0, 1, ..., 23].")


def _validate_generation_data(generation_data: dict) -> None:
    _require_dict(generation_data, "generation_data")
    required_keys = ("solar", "wind")
    _require_keys(generation_data, required_keys, "generation_data")

    for key in required_keys:
        field_name = f"generation_data['{key}']"
        _require_list_of_numbers(generation_data[key], field_name, length=_HOURS_IN_DAY)
        _require_non_negative(generation_data[key], field_name)


def _find_consumption_key(generation_data: dict) -> Optional[str]:
    for key in _CONSUMPTION_KEYS:
        if key in generation_data:
            return key
    return None


def _weighted_daily_cost(hourly_costs: Sequence[float], hourly_generation: Sequence[float]) -> float:
    total_generation = sum(hourly_generation)
    if total_generation == 0:
        return float("inf")
    total_cost = sum(cost * generation for cost, generation in zip(hourly_costs, hourly_generation))
    return total_cost / total_generation


def _build_lot_hourly_breakdown(
    hours: Sequence[float],
    solar_hourly_costs: Sequence[float],
    wind_hourly_costs: Sequence[float],
    solar_generation: Sequence[float],
    wind_generation: Sequence[float],
    consumption: Sequence[float],
) -> List[Dict[str, float]]:
    lot_hourly = []
    for hour, solar_cost, wind_cost, solar_gen, wind_gen, consumed in zip(
        hours, solar_hourly_costs, wind_hourly_costs, solar_generation, wind_generation, consumption
    ):
        produced = solar_gen + wind_gen
        used_from_lot = min(produced, consumed)
        total_generation_cost = solar_cost * solar_gen + wind_cost * wind_gen
        price = random.uniform(PRICE_MIN_PER_KWH, PRICE_MAX_PER_KWH)
        revenue = price * used_from_lot
        profit = revenue - total_generation_cost
        lot_cost = float("inf") if used_from_lot == 0 else total_generation_cost / used_from_lot

        lot_hourly.append(
            {
                "hour": int(hour),
                "produced": produced,
                "consumed": consumed,
                "used_from_lot": used_from_lot,
                "cost": lot_cost,
                "price": price,
                "revenue": revenue,
                "profit": profit,
                "generation_cost": total_generation_cost,
            }
        )
    return lot_hourly


def _daily_lot_cost(lot_hourly: Sequence[Dict[str, float]]) -> float:
    used_total = sum(hour_row["used_from_lot"] for hour_row in lot_hourly)
    if used_total == 0:
        return float("inf")
    total_cost = sum(hour_row["generation_cost"] for hour_row in lot_hourly)
    return total_cost / used_total


def calculate_cost(weather_data, generation_data):
    """Return cost metrics for solar/wind and optional hourly lot cost."""
    _validate_weather_data(weather_data)
    _validate_generation_data(generation_data)

    temperature = weather_data["temperature"]
    wind_speed = weather_data["wind_speed"]
    solar_generation = generation_data["solar"]
    wind_generation = generation_data["wind"]

    solar_hourly_costs = [
        SOLAR_BASE_COST * (1 + SOLAR_TEMP_PENALTY * abs(temp - SOLAR_TEMP_OPTIMAL))
        for temp in temperature
    ]
    wind_hourly_costs = [
        WIND_BASE_COST * (1 + WIND_WEAR_PENALTY * max(0.0, speed - WIND_WEAR_THRESHOLD))
        for speed in wind_speed
    ]

    result = {
        "solar": _weighted_daily_cost(solar_hourly_costs, solar_generation),
        "wind": _weighted_daily_cost(wind_hourly_costs, wind_generation),
    }

    consumption_key = _find_consumption_key(generation_data)
    if consumption_key is not None:
        _require_list_of_numbers(
            generation_data[consumption_key],
            f"generation_data['{consumption_key}']",
            length=_HOURS_IN_DAY,
        )
        _require_non_negative(generation_data[consumption_key], f"generation_data['{consumption_key}']")

        lot_hourly = _build_lot_hourly_breakdown(
            weather_data["hours"],
            solar_hourly_costs,
            wind_hourly_costs,
            solar_generation,
            wind_generation,
            generation_data[consumption_key],
        )
        result["lot_hourly"] = lot_hourly
        result["lot"] = _daily_lot_cost(lot_hourly)
        result["hourly_profit"] = [hour_row["profit"] for hour_row in lot_hourly]
        result["profit"] = sum(result["hourly_profit"])

    return result
