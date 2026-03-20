import pandas as pd

def calculate_generation(weather_data):

    results = []
    for _, row in weather_data.iterrows():
        solar = row['Облачность'] * 1.1 - 4.1
        solar = max(0, solar)  
        
        wind = row['Ветер'] * 1.70 + 2.3
        
        results.append({
            'Тики': row['Время'],
            'СЭС': round(solar, 2),
            'Ветряк': round(wind, 2),
            'Всего': round(solar + wind, 2)
        })
    
    #total_solar = sum(r['СЭС'] for r in results)
    #total_wind = sum(r['Ветряк'] for r in results)
    #total_all = total_solar + total_wind
    
    #results.append({
        #'Тики': 'ИТОГО:',
        #'СЭС': round(total_solar, 2),
        #'Ветряк': round(total_wind, 2),
        #'Всего': round(total_all, 2)
   # })
    
    df_results = pd.DataFrame(results)
    return df_results

