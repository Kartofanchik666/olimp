import pandas as pd
def calculate_generation(weather_data):
  results = []
  for _, row in weather_data.iterrows(weather_data):
      results.append({'Тики': row['Время'] , 'СЭС': row['Облачность']*0.1-4.1, 'Ветряк': row['Ветер']*0.70+2.3})
  calculate_generation = pd.DataFrame(results)
  print(calculate_generation.to_string(index=False)) 
pass
